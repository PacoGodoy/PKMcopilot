"""
analysis/card_analyzer.py
Version: 1.0
Last updated: 2025-01-21

Comprehensive analytical module for processing Pokémon TCG card database.
This module provides in-depth analysis of card features, semantic processing,
role categorization, pros/cons analysis, and synergy detection.

Technologies used:
- SQLite for card database access
- spaCy for NLP and semantic analysis
- scikit-learn for ML-based categorization
- pandas for data manipulation
- numpy for numerical operations

Main functionality:
1. Card feature extraction from database
2. NLP-based semantic analysis of card text
3. ML-based role categorization with confidence scores
4. Pros/cons analysis based on extracted features
5. Intra-card and inter-card synergy detection
6. Archetype evaluation and recommendations
"""

import sqlite3
import json
import re
import logging
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import numpy as np
import pandas as pd

# NLP and ML imports
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CardFeatures:
    """Comprehensive card feature representation"""
    card_id: str
    name: str
    supertype: str
    subtype: str
    hp: Optional[int]
    types: List[str]
    retreat_cost: Optional[int]
    attacks: List[Dict[str, Any]]
    abilities: List[Dict[str, Any]]
    rules: List[str]
    expansion: str
    rarity: str
    
    # Extracted features
    semantic_keywords: List[str]
    numerical_effects: Dict[str, int]
    conditions: List[str]
    roles: Dict[str, float]  # role -> confidence
    pros: List[str]
    cons: List[str]
    synergy_tags: List[str]

@dataclass
class SynergyAnalysis:
    """Results of synergy analysis"""
    intra_card_score: float
    inter_card_synergies: List[Tuple[str, str, float]]  # card1, card2, score
    archetype_fit: Dict[str, float]  # archetype -> score
    recommendations: List[Dict[str, Any]]

class CardAnalyzer:
    """
    Comprehensive card analyzer for Pokémon TCG cards.
    Provides feature extraction, NLP analysis, ML categorization, and synergy detection.
    """
    
    # Define card roles and archetypes
    POKEMON_ROLES = [
        'main_attacker', 'secondary_attacker', 'setup_pokemon', 'wall', 'pivot',
        'energy_acceleration', 'draw_engine', 'disruptor', 'utility', 'tech'
    ]
    
    TRAINER_ROLES = [
        'draw_supporter', 'search_supporter', 'disruption_supporter', 
        'search_item', 'draw_item', 'utility_item', 'tool', 'stadium'
    ]
    
    ENERGY_ROLES = [
        'basic_energy', 'special_energy', 'acceleration', 'utility'
    ]
    
    ARCHETYPES = [
        'aggro', 'control', 'toolbox', 'engine', 'midrange', 'combo', 'stall'
    ]
    
    # Semantic keywords for different effects
    SEMANTIC_PATTERNS = {
        'draw': ['draw', 'reveal', 'look at', 'search', 'put into hand'],
        'damage': ['damage', 'knock out', 'destroy', 'discard', 'put damage'],
        'energy': ['energy', 'attach', 'accelerate', 'basic energy', 'special energy'],
        'heal': ['heal', 'remove damage', 'restore', 'recover'],
        'disrupt': ['discard', 'shuffle', 'prevent', 'block', 'switch'],
        'setup': ['bench', 'play', 'put into play', 'evolve', 'search'],
        'protection': ['prevent', 'immune', 'resist', 'protect', 'cannot be'],
        'movement': ['switch', 'retreat', 'return', 'move', 'swap']
    }
    
    def __init__(self, db_path: str = "data/cards.db"):
        """
        Initialize the CardAnalyzer with database connection and NLP model.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.nlp = None
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.role_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        
        # Initialize components
        self._load_nlp_model()
        self._initialize_database_connection()
        
        logger.info("CardAnalyzer initialized successfully")
    
    def _load_nlp_model(self) -> None:
        """Load spaCy NLP model with error handling"""
        try:
            self.nlp = spacy.load('en_core_web_sm')
            logger.info("spaCy model loaded successfully")
        except OSError as e:
            logger.error(f"Failed to load spaCy model: {e}")
            logger.info("Please install the English model: python -m spacy download en_core_web_sm")
            raise
    
    def _initialize_database_connection(self) -> None:
        """Initialize database connection and verify schema"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM cards")
                count = cursor.fetchone()[0]
                logger.info(f"Database connected. Found {count} cards in database")
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    def extract_card_features(self, card_id: Optional[str] = None) -> List[CardFeatures]:
        """
        Extract comprehensive features from cards in the database.
        
        Args:
            card_id: Optional specific card ID to analyze. If None, processes all cards.
            
        Returns:
            List of CardFeatures objects with extracted data
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                if card_id:
                    query = "SELECT * FROM cards WHERE card_id = ?"
                    cursor = conn.execute(query, (card_id,))
                else:
                    query = "SELECT * FROM cards"
                    cursor = conn.execute(query)
                
                cards_data = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                
            logger.info(f"Processing {len(cards_data)} cards for feature extraction")
            
            features_list = []
            for card_data in cards_data:
                card_dict = dict(zip(columns, card_data))
                features = self._extract_single_card_features(card_dict)
                features_list.append(features)
            
            return features_list
            
        except Exception as e:
            logger.error(f"Error extracting card features: {e}")
            raise
    
    def _extract_single_card_features(self, card_data: Dict[str, Any]) -> CardFeatures:
        """
        Extract features from a single card's database record.
        
        Args:
            card_data: Dictionary containing card data from database
            
        Returns:
            CardFeatures object with extracted and analyzed features
        """
        try:
            # Parse basic card information
            card_id = card_data.get('card_id', '')
            name = card_data.get('name', '')
            supertype = card_data.get('supertype', '')
            subtype = card_data.get('subtype', '')
            hp = card_data.get('hp')
            types = self._parse_types(card_data.get('types', ''))
            retreat_cost = card_data.get('retreat_cost')
            expansion = card_data.get('expansion', '')
            rarity = card_data.get('rarity', '')
            
            # Parse complex fields (stored as JSON strings)
            attacks = self._parse_attacks(card_data.get('attacks', ''))
            abilities = self._parse_abilities(card_data.get('abilities', ''))
            rules = self._parse_rules(card_data.get('rules', ''))
            
            # Extract semantic features using NLP
            all_text = self._combine_card_text(attacks, abilities, rules)
            semantic_keywords = self._extract_semantic_keywords(all_text)
            
            # Extract numerical effects and conditions
            numerical_effects = self._extract_numerical_effects(all_text)
            conditions = self._extract_conditions(all_text)
            
            # Categorize card roles using ML
            roles = self._categorize_card_roles(card_data, semantic_keywords, numerical_effects)
            
            # Analyze pros and cons
            pros, cons = self._analyze_pros_cons(card_data, semantic_keywords, numerical_effects)
            
            # Generate synergy tags
            synergy_tags = self._generate_synergy_tags(semantic_keywords, supertype, types)
            
            return CardFeatures(
                card_id=card_id,
                name=name,
                supertype=supertype,
                subtype=subtype,
                hp=hp,
                types=types,
                retreat_cost=retreat_cost,
                attacks=attacks,
                abilities=abilities,
                rules=rules,
                expansion=expansion,
                rarity=rarity,
                semantic_keywords=semantic_keywords,
                numerical_effects=numerical_effects,
                conditions=conditions,
                roles=roles,
                pros=pros,
                cons=cons,
                synergy_tags=synergy_tags
            )
            
        except Exception as e:
            logger.error(f"Error extracting features for card {card_data.get('card_id', 'unknown')}: {e}")
            raise
    
    def _parse_types(self, types_str: str) -> List[str]:
        """Parse types from database string representation"""
        if not types_str:
            return []
        try:
            return json.loads(types_str) if types_str.startswith('[') else [types_str]
        except json.JSONDecodeError:
            return types_str.split(',') if types_str else []
    
    def _parse_attacks(self, attacks_str: str) -> List[Dict[str, Any]]:
        """Parse attacks from database string representation"""
        if not attacks_str:
            return []
        try:
            return json.loads(attacks_str) if attacks_str.startswith('[') else []
        except json.JSONDecodeError:
            return []
    
    def _parse_abilities(self, abilities_str: str) -> List[Dict[str, Any]]:
        """Parse abilities from database string representation"""
        if not abilities_str:
            return []
        try:
            return json.loads(abilities_str) if abilities_str.startswith('[') else []
        except json.JSONDecodeError:
            return []
    
    def _parse_rules(self, rules_str: str) -> List[str]:
        """Parse rules from database string representation"""
        if not rules_str:
            return []
        try:
            return json.loads(rules_str) if rules_str.startswith('[') else [rules_str]
        except json.JSONDecodeError:
            return [rules_str] if rules_str else []
    
    def _combine_card_text(self, attacks: List[Dict], abilities: List[Dict], rules: List[str]) -> str:
        """Combine all card text for NLP processing"""
        text_parts = []
        
        # Add attack text
        for attack in attacks:
            if 'text' in attack and attack['text']:
                text_parts.append(attack['text'])
            if 'name' in attack and attack['name']:
                text_parts.append(attack['name'])
        
        # Add ability text
        for ability in abilities:
            if 'text' in ability and ability['text']:
                text_parts.append(ability['text'])
            if 'name' in ability and ability['name']:
                text_parts.append(ability['name'])
        
        # Add rules text
        text_parts.extend(rules)
        
        return ' '.join(text_parts)
    
    def _extract_semantic_keywords(self, text: str) -> List[str]:
        """
        Extract semantic keywords from card text using NLP and pattern matching.
        
        Args:
            text: Combined card text
            
        Returns:
            List of semantic keywords found in the text
        """
        if not text or not self.nlp:
            return []
        
        keywords = []
        text_lower = text.lower()
        
        # Use pattern matching for known semantic categories
        for category, patterns in self.SEMANTIC_PATTERNS.items():
            for pattern in patterns:
                if pattern in text_lower:
                    keywords.append(category)
                    break
        
        # Use spaCy for additional semantic analysis
        try:
            doc = self.nlp(text)
            
            # Extract important verbs and nouns
            for token in doc:
                if (token.pos_ in ['VERB', 'NOUN'] and 
                    not token.is_stop and 
                    len(token.text) > 2 and
                    token.text.lower() not in ['card', 'cards', 'pokemon', 'turn']):
                    keywords.append(token.lemma_.lower())
            
            # Extract named entities
            for ent in doc.ents:
                if ent.label_ in ['CARDINAL', 'ORDINAL']:  # Numbers
                    continue
                keywords.append(ent.text.lower())
                
        except Exception as e:
            logger.warning(f"NLP processing failed: {e}")
        
        return list(set(keywords))
    
    def _extract_numerical_effects(self, text: str) -> Dict[str, int]:
        """
        Extract numerical values from card effects.
        
        Args:
            text: Card text to analyze
            
        Returns:
            Dictionary mapping effect types to numerical values
        """
        numerical_effects = {}
        
        if not text:
            return numerical_effects
        
        # Common numerical patterns in Pokémon TCG
        patterns = {
            'draw_amount': r'draw (\d+)',
            'damage_amount': r'(\d+) damage',
            'discard_amount': r'discard (\d+)',
            'search_amount': r'search.*?(\d+)',
            'energy_cost': r'(\d+).*?energy',
            'heal_amount': r'heal (\d+)',
        }
        
        for effect_type, pattern in patterns.items():
            matches = re.findall(pattern, text.lower())
            if matches:
                # Take the maximum value if multiple matches
                numerical_effects[effect_type] = max(int(match) for match in matches)
        
        return numerical_effects
    
    def _extract_conditions(self, text: str) -> List[str]:
        """
        Extract conditions and requirements from card text.
        
        Args:
            text: Card text to analyze
            
        Returns:
            List of conditions found
        """
        conditions = []
        
        if not text:
            return conditions
        
        text_lower = text.lower()
        
        # Common condition patterns
        condition_patterns = [
            'if ', 'when ', 'once during', 'only if', 'before you',
            'after you', 'during your turn', 'flip a coin', 'discard'
        ]
        
        for pattern in condition_patterns:
            if pattern in text_lower:
                conditions.append(pattern.strip())
        
        return list(set(conditions))
    
    def _categorize_card_roles(self, card_data: Dict, keywords: List[str], effects: Dict[str, int]) -> Dict[str, float]:
        """
        Categorize card roles using rule-based logic and ML patterns.
        
        Args:
            card_data: Raw card data
            keywords: Extracted semantic keywords
            effects: Extracted numerical effects
            
        Returns:
            Dictionary mapping roles to confidence scores
        """
        roles = {}
        supertype = card_data.get('supertype', '').lower()
        
        try:
            if supertype == 'pokémon':
                roles = self._categorize_pokemon_roles(card_data, keywords, effects)
            elif supertype == 'trainer':
                roles = self._categorize_trainer_roles(card_data, keywords, effects)
            elif supertype == 'energy':
                roles = self._categorize_energy_roles(card_data, keywords, effects)
            
            # Normalize confidence scores
            total = sum(roles.values())
            if total > 0:
                roles = {role: score/total for role, score in roles.items()}
        
        except Exception as e:
            logger.warning(f"Role categorization failed: {e}")
        
        return roles
    
    def _categorize_pokemon_roles(self, card_data: Dict, keywords: List[str], effects: Dict[str, int]) -> Dict[str, float]:
        """Categorize Pokémon card roles"""
        roles = {}
        hp = card_data.get('hp', 0) or 0
        retreat_cost = card_data.get('retreat_cost', 0) or 0
        
        # Main attacker: high HP, high damage attacks
        if hp >= 200 or effects.get('damage_amount', 0) >= 150:
            roles['main_attacker'] = 0.8
        elif hp >= 120 or effects.get('damage_amount', 0) >= 80:
            roles['secondary_attacker'] = 0.6
        
        # Setup Pokemon: draw/search abilities
        if 'draw' in keywords or 'search' in keywords:
            roles['setup_pokemon'] = 0.7
        
        # Wall: high HP, defensive abilities
        if hp >= 200 or 'protection' in keywords or 'heal' in keywords:
            roles['wall'] = 0.6
        
        # Pivot: low retreat cost or switching abilities
        if retreat_cost == 0 or 'movement' in keywords:
            roles['pivot'] = 0.7
        
        # Energy acceleration
        if 'energy' in keywords and 'attach' in keywords:
            roles['energy_acceleration'] = 0.8
        
        # Draw engine
        if effects.get('draw_amount', 0) >= 2:
            roles['draw_engine'] = 0.7
        
        # Disruptor
        if 'disrupt' in keywords or effects.get('discard_amount', 0) > 0:
            roles['disruptor'] = 0.6
        
        return roles
    
    def _categorize_trainer_roles(self, card_data: Dict, keywords: List[str], effects: Dict[str, int]) -> Dict[str, float]:
        """Categorize Trainer card roles"""
        roles = {}
        subtype = card_data.get('subtype', '').lower()
        
        if subtype == 'supporter':
            if 'draw' in keywords or effects.get('draw_amount', 0) > 0:
                roles['draw_supporter'] = 0.9
            elif 'search' in keywords:
                roles['search_supporter'] = 0.8
            elif 'disrupt' in keywords:
                roles['disruption_supporter'] = 0.7
        
        elif subtype == 'item':
            if 'search' in keywords:
                roles['search_item'] = 0.8
            elif 'draw' in keywords:
                roles['draw_item'] = 0.7
            else:
                roles['utility_item'] = 0.6
        
        elif subtype == 'pokémon tool':
            roles['tool'] = 0.9
        
        elif subtype == 'stadium':
            roles['stadium'] = 0.9
        
        return roles
    
    def _categorize_energy_roles(self, card_data: Dict, keywords: List[str], effects: Dict[str, int]) -> Dict[str, float]:
        """Categorize Energy card roles"""
        roles = {}
        name = card_data.get('name', '').lower()
        
        if 'basic' in name and 'energy' in name:
            roles['basic_energy'] = 0.9
        else:
            roles['special_energy'] = 0.8
            
            if 'acceleration' in keywords or 'attach' in keywords:
                roles['acceleration'] = 0.7
            
            if any(keyword in keywords for keyword in ['draw', 'heal', 'protection']):
                roles['utility'] = 0.6
        
        return roles
    
    def _analyze_pros_cons(self, card_data: Dict, keywords: List[str], effects: Dict[str, int]) -> Tuple[List[str], List[str]]:
        """
        Analyze card strengths and weaknesses.
        
        Args:
            card_data: Raw card data
            keywords: Extracted semantic keywords
            effects: Extracted numerical effects
            
        Returns:
            Tuple of (pros, cons) lists
        """
        pros = []
        cons = []
        
        try:
            hp = card_data.get('hp', 0) or 0
            retreat_cost = card_data.get('retreat_cost', 0) or 0
            supertype = card_data.get('supertype', '').lower()
            
            if supertype == 'pokémon':
                # HP analysis
                if hp >= 250:
                    pros.append("Very high HP for survivability")
                elif hp >= 180:
                    pros.append("Good HP for tanking hits")
                elif hp <= 70:
                    cons.append("Low HP, vulnerable to knockouts")
                
                # Retreat cost analysis
                if retreat_cost == 0:
                    pros.append("Free retreat for easy pivoting")
                elif retreat_cost >= 3:
                    cons.append("High retreat cost limits mobility")
                
                # Attack analysis
                damage = effects.get('damage_amount', 0)
                if damage >= 200:
                    pros.append("High damage output")
                elif damage >= 120:
                    pros.append("Decent damage for prizes")
                elif damage <= 60:
                    cons.append("Low damage output")
            
            # Keyword-based analysis
            if 'draw' in keywords:
                draw_amount = effects.get('draw_amount', 1)
                if draw_amount >= 3:
                    pros.append(f"Strong draw power ({draw_amount} cards)")
                else:
                    pros.append("Provides card draw")
            
            if 'search' in keywords:
                pros.append("Tutoring effect for consistency")
            
            if 'energy' in keywords and 'attach' in keywords:
                pros.append("Energy acceleration capability")
            
            if 'protection' in keywords:
                pros.append("Defensive capabilities")
            
            if 'disrupt' in keywords:
                pros.append("Disruption potential")
            
            # Condition-based cons
            if 'flip a coin' in ' '.join(effects.get('conditions', [])):
                cons.append("Relies on coin flips (inconsistent)")
            
            if effects.get('discard_amount', 0) > 0:
                cons.append("Requires discarding resources")
        
        except Exception as e:
            logger.warning(f"Pros/cons analysis failed: {e}")
        
        return pros, cons
    
    def _generate_synergy_tags(self, keywords: List[str], supertype: str, types: List[str]) -> List[str]:
        """
        Generate synergy tags for card interactions.
        
        Args:
            keywords: Semantic keywords
            supertype: Card supertype
            types: Pokémon types if applicable
            
        Returns:
            List of synergy tags
        """
        tags = []
        
        # Add type-based synergy tags
        tags.extend(types)
        
        # Add effect-based synergy tags
        for keyword in keywords:
            if keyword in ['draw', 'search', 'energy', 'heal', 'disrupt']:
                tags.append(f"{keyword}_synergy")
        
        # Add supertype tag
        tags.append(f"{supertype.lower()}_synergy")
        
        return list(set(tags))
    
    def detect_synergies(self, decklist: Dict[str, int], card_features: List[CardFeatures]) -> SynergyAnalysis:
        """
        Detect synergies within a decklist and analyze archetype fit.
        
        Args:
            decklist: Dictionary mapping card names to quantities
            card_features: List of CardFeatures for all relevant cards
            
        Returns:
            SynergyAnalysis object with detailed synergy information
        """
        try:
            # Create card lookup by name
            card_lookup = {features.name: features for features in card_features}
            
            # Get features for cards in the decklist
            deck_cards = []
            for card_name, quantity in decklist.items():
                if card_name in card_lookup:
                    deck_cards.extend([card_lookup[card_name]] * quantity)
            
            # Calculate intra-card synergy
            intra_card_score = self._calculate_intra_card_synergy(deck_cards)
            
            # Calculate inter-card synergies
            inter_card_synergies = self._calculate_inter_card_synergies(deck_cards)
            
            # Evaluate archetype fit
            archetype_fit = self._evaluate_archetype_fit(deck_cards)
            
            # Generate recommendations
            recommendations = self._generate_deck_recommendations(deck_cards, archetype_fit)
            
            return SynergyAnalysis(
                intra_card_score=intra_card_score,
                inter_card_synergies=inter_card_synergies,
                archetype_fit=archetype_fit,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Synergy detection failed: {e}")
            raise
    
    def _calculate_intra_card_synergy(self, deck_cards: List[CardFeatures]) -> float:
        """Calculate synergy between abilities and attacks within individual cards"""
        total_synergy = 0.0
        count = 0
        
        for card in deck_cards:
            if card.abilities and card.attacks:
                # Check for keyword overlap between abilities and attacks
                ability_keywords = set()
                attack_keywords = set()
                
                for ability in card.abilities:
                    ability_text = ability.get('text', '')
                    ability_keywords.update(self._extract_semantic_keywords(ability_text))
                
                for attack in card.attacks:
                    attack_text = attack.get('text', '')
                    attack_keywords.update(self._extract_semantic_keywords(attack_text))
                
                overlap = len(ability_keywords.intersection(attack_keywords))
                synergy_score = overlap / max(len(ability_keywords), len(attack_keywords), 1)
                total_synergy += synergy_score
                count += 1
        
        return total_synergy / max(count, 1)
    
    def _calculate_inter_card_synergies(self, deck_cards: List[CardFeatures]) -> List[Tuple[str, str, float]]:
        """Calculate synergies between different cards in the deck"""
        synergies = []
        
        for i, card1 in enumerate(deck_cards):
            for j, card2 in enumerate(deck_cards[i+1:], i+1):
                if card1.card_id != card2.card_id:
                    synergy_score = self._calculate_pair_synergy(card1, card2)
                    if synergy_score > 0.3:  # Only include significant synergies
                        synergies.append((card1.name, card2.name, synergy_score))
        
        # Sort by synergy score and return top synergies
        synergies.sort(key=lambda x: x[2], reverse=True)
        return synergies[:10]
    
    def _calculate_pair_synergy(self, card1: CardFeatures, card2: CardFeatures) -> float:
        """Calculate synergy score between two specific cards"""
        synergy_score = 0.0
        
        # Check synergy tag overlap
        tag_overlap = len(set(card1.synergy_tags).intersection(set(card2.synergy_tags)))
        synergy_score += tag_overlap * 0.2
        
        # Check complementary roles
        if self._are_roles_complementary(card1.roles, card2.roles):
            synergy_score += 0.4
        
        # Check type synergy for Pokémon
        if card1.supertype == 'Pokémon' and card2.supertype == 'Pokémon':
            if set(card1.types).intersection(set(card2.types)):
                synergy_score += 0.3
        
        # Check keyword synergy
        keyword_overlap = len(set(card1.semantic_keywords).intersection(set(card2.semantic_keywords)))
        synergy_score += keyword_overlap * 0.1
        
        return min(synergy_score, 1.0)
    
    def _are_roles_complementary(self, roles1: Dict[str, float], roles2: Dict[str, float]) -> bool:
        """Check if two cards have complementary roles"""
        complementary_pairs = [
            ('main_attacker', 'setup_pokemon'),
            ('main_attacker', 'energy_acceleration'),
            ('draw_engine', 'main_attacker'),
            ('search_item', 'main_attacker'),
            ('wall', 'pivot'),
        ]
        
        for role1, role2 in complementary_pairs:
            if (role1 in roles1 and role2 in roles2) or (role2 in roles1 and role1 in roles2):
                return True
        
        return False
    
    def _evaluate_archetype_fit(self, deck_cards: List[CardFeatures]) -> Dict[str, float]:
        """Evaluate how well the deck fits different archetypes"""
        archetype_scores = {archetype: 0.0 for archetype in self.ARCHETYPES}
        
        # Count roles in the deck
        role_counts = defaultdict(int)
        for card in deck_cards:
            for role in card.roles:
                role_counts[role] += 1
        
        total_cards = len(deck_cards)
        if total_cards == 0:
            return archetype_scores
        
        # Evaluate each archetype
        # Aggro: focus on attackers, low setup
        aggro_score = (role_counts.get('main_attacker', 0) + role_counts.get('secondary_attacker', 0)) / total_cards
        archetype_scores['aggro'] = min(aggro_score, 1.0)
        
        # Control: focus on disruption, draw, defensive cards
        control_score = (role_counts.get('disruptor', 0) + role_counts.get('draw_engine', 0) + role_counts.get('wall', 0)) / total_cards
        archetype_scores['control'] = min(control_score, 1.0)
        
        # Engine: focus on consistency and setup
        engine_score = (role_counts.get('draw_engine', 0) + role_counts.get('setup_pokemon', 0) + role_counts.get('search_item', 0)) / total_cards
        archetype_scores['engine'] = min(engine_score, 1.0)
        
        # Toolbox: diverse utility cards
        utility_score = (role_counts.get('utility', 0) + role_counts.get('tech', 0) + role_counts.get('pivot', 0)) / total_cards
        archetype_scores['toolbox'] = min(utility_score, 1.0)
        
        # Combo: specific synergy patterns
        combo_score = role_counts.get('energy_acceleration', 0) / total_cards
        archetype_scores['combo'] = min(combo_score, 1.0)
        
        # Stall: defensive focus
        stall_score = (role_counts.get('wall', 0) + role_counts.get('heal', 0)) / total_cards
        archetype_scores['stall'] = min(stall_score, 1.0)
        
        # Midrange: balanced approach
        balance_score = 1.0 - max(archetype_scores.values())
        archetype_scores['midrange'] = max(balance_score, 0.0)
        
        return archetype_scores
    
    def _generate_deck_recommendations(self, deck_cards: List[CardFeatures], archetype_fit: Dict[str, float]) -> List[Dict[str, Any]]:
        """Generate tactical recommendations for deck improvement"""
        recommendations = []
        
        try:
            # Determine primary archetype
            primary_archetype = max(archetype_fit.items(), key=lambda x: x[1])[0]
            
            # Count current roles
            role_counts = defaultdict(int)
            for card in deck_cards:
                for role in card.roles:
                    role_counts[role] += 1
            
            total_cards = len(deck_cards)
            
            # Generate archetype-specific recommendations
            if primary_archetype == 'aggro':
                if role_counts.get('main_attacker', 0) < total_cards * 0.3:
                    recommendations.append({
                        'type': 'inclusion',
                        'suggestion': 'Add more main attackers',
                        'reason': 'Aggro decks need consistent attacking threats',
                        'priority': 'high'
                    })
                
                if role_counts.get('energy_acceleration', 0) < 2:
                    recommendations.append({
                        'type': 'inclusion',
                        'suggestion': 'Include energy acceleration',
                        'reason': 'Speed up setup for aggressive plays',
                        'priority': 'medium'
                    })
            
            elif primary_archetype == 'control':
                if role_counts.get('draw_engine', 0) < 4:
                    recommendations.append({
                        'type': 'inclusion',
                        'suggestion': 'Add more draw power',
                        'reason': 'Control decks need card advantage',
                        'priority': 'high'
                    })
                
                if role_counts.get('disruptor', 0) < 2:
                    recommendations.append({
                        'type': 'inclusion',
                        'suggestion': 'Include disruption cards',
                        'reason': 'Disrupt opponent strategy and buy time',
                        'priority': 'high'
                    })
            
            elif primary_archetype == 'engine':
                if role_counts.get('setup_pokemon', 0) < 2:
                    recommendations.append({
                        'type': 'inclusion',
                        'suggestion': 'Add setup Pokémon',
                        'reason': 'Engine decks need consistent setup',
                        'priority': 'high'
                    })
            
            # General recommendations
            if role_counts.get('pivot', 0) == 0:
                recommendations.append({
                    'type': 'inclusion',
                    'suggestion': 'Consider pivot Pokémon',
                    'reason': 'Improve board positioning and retreat options',
                    'priority': 'low'
                })
            
            # Check for potential dead cards (cards with low synergy)
            low_synergy_cards = []
            for card in deck_cards:
                if len(card.synergy_tags) < 2:
                    low_synergy_cards.append(card.name)
            
            if low_synergy_cards:
                recommendations.append({
                    'type': 'exclusion',
                    'suggestion': f'Consider removing: {", ".join(set(low_synergy_cards[:3]))}',
                    'reason': 'These cards have limited synergy with the deck',
                    'priority': 'medium'
                })
        
        except Exception as e:
            logger.warning(f"Recommendation generation failed: {e}")
        
        return recommendations
    
    def generate_comprehensive_report(self, card_features: List[CardFeatures], 
                                    synergy_analysis: Optional[SynergyAnalysis] = None) -> Dict[str, Any]:
        """
        Generate a comprehensive analysis report.
        
        Args:
            card_features: List of analyzed card features
            synergy_analysis: Optional synergy analysis results
            
        Returns:
            Dictionary containing comprehensive analysis report
        """
        try:
            report = {
                'summary': {
                    'total_cards_analyzed': len(card_features),
                    'analysis_timestamp': pd.Timestamp.now().isoformat(),
                },
                'card_analysis': [],
                'role_distribution': self._calculate_role_distribution(card_features),
                'archetype_analysis': None,
                'synergy_report': None,
                'recommendations': []
            }
            
            # Add individual card analysis
            for card in card_features:
                card_report = {
                    'name': card.name,
                    'type': f"{card.supertype} - {card.subtype}",
                    'primary_roles': [role for role, conf in sorted(card.roles.items(), 
                                                                   key=lambda x: x[1], reverse=True)[:3]],
                    'top_pros': card.pros[:3],
                    'main_cons': card.cons[:3],
                    'synergy_potential': len(card.synergy_tags),
                    'semantic_keywords': card.semantic_keywords[:5]
                }
                report['card_analysis'].append(card_report)
            
            # Add synergy analysis if provided
            if synergy_analysis:
                report['synergy_report'] = {
                    'intra_card_synergy_score': round(synergy_analysis.intra_card_score, 3),
                    'top_synergies': [
                        {
                            'card1': synergy[0],
                            'card2': synergy[1],
                            'score': round(synergy[2], 3)
                        }
                        for synergy in synergy_analysis.inter_card_synergies[:5]
                    ],
                    'archetype_fit': {
                        arch: round(score, 3) 
                        for arch, score in sorted(synergy_analysis.archetype_fit.items(), 
                                                key=lambda x: x[1], reverse=True)
                    },
                    'recommendations': synergy_analysis.recommendations
                }
                
                report['archetype_analysis'] = synergy_analysis.archetype_fit
                report['recommendations'] = synergy_analysis.recommendations
            
            logger.info(f"Generated comprehensive report for {len(card_features)} cards")
            return report
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            raise
    
    def _calculate_role_distribution(self, card_features: List[CardFeatures]) -> Dict[str, int]:
        """Calculate distribution of roles across all cards"""
        role_counts = defaultdict(int)
        
        for card in card_features:
            for role in card.roles:
                role_counts[role] += 1
        
        return dict(role_counts)

def main():
    """
    Example usage of the CardAnalyzer module.
    This function demonstrates the main capabilities of the analyzer.
    """
    try:
        # Initialize analyzer
        analyzer = CardAnalyzer()
        
        # Extract features from all cards in database
        card_features = analyzer.extract_card_features()
        
        if not card_features:
            logger.warning("No cards found in database. Please populate the database first.")
            return
        
        # Example decklist for synergy analysis
        example_decklist = {
            "Charizard ex": 2,
            "Charmander": 4,
            "Charmeleon": 2,
            "Professor's Research": 4,
            "Ultra Ball": 4,
            "Fire Energy": 8
        }
        
        # Analyze synergies
        synergy_analysis = analyzer.detect_synergies(example_decklist, card_features)
        
        # Generate comprehensive report
        report = analyzer.generate_comprehensive_report(card_features, synergy_analysis)
        
        # Print summary
        print("=== CardAnalyzer Report Summary ===")
        print(f"Cards analyzed: {report['summary']['total_cards_analyzed']}")
        print(f"Analysis timestamp: {report['summary']['analysis_timestamp']}")
        
        if report['synergy_report']:
            print(f"\nSynergy Analysis:")
            print(f"Intra-card synergy score: {report['synergy_report']['intra_card_synergy_score']}")
            print(f"Top archetype fit: {max(report['archetype_analysis'].items(), key=lambda x: x[1])}")
            print(f"Recommendations: {len(report['recommendations'])}")
        
        print(f"\nRole distribution:")
        for role, count in sorted(report['role_distribution'].items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {role}: {count}")
        
        logger.info("CardAnalyzer demonstration completed successfully")
        
    except Exception as e:
        logger.error(f"CardAnalyzer demonstration failed: {e}")
        raise

if __name__ == "__main__":
    main()