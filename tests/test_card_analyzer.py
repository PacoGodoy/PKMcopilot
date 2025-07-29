"""
tests/test_card_analyzer.py

Unit tests for the comprehensive card analyzer module.
Tests the main functionality including feature extraction, role categorization,
synergy detection, and report generation.
"""

import unittest
import sqlite3
import json
import tempfile
import os
from unittest.mock import patch, MagicMock

# Import the module to test
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.card_analyzer import CardAnalyzer, CardFeatures, SynergyAnalysis

class TestCardAnalyzer(unittest.TestCase):
    """Test cases for CardAnalyzer functionality"""
    
    def setUp(self):
        """Set up test database with sample data"""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # Initialize database schema
        self._create_test_database()
        self._insert_test_data()
        
        # Mock spaCy to avoid dependency issues in tests
        self.spacy_mock = MagicMock()
        self.nlp_mock = MagicMock()
        self.spacy_mock.load.return_value = self.nlp_mock
        
        # Mock spaCy doc processing
        token_mock = MagicMock()
        token_mock.pos_ = 'VERB'
        token_mock.is_stop = False
        token_mock.text = 'attack'
        token_mock.lemma_ = 'attack'
        
        doc_mock = MagicMock()
        doc_mock.__iter__ = MagicMock(return_value=iter([token_mock]))
        doc_mock.ents = []
        
        self.nlp_mock.return_value = doc_mock
        
    def tearDown(self):
        """Clean up test database"""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def _create_test_database(self):
        """Create test database with proper schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE cards (
            card_id TEXT PRIMARY KEY,
            name TEXT,
            supertype TEXT,
            subtype TEXT,
            hp INTEGER,
            types TEXT,
            retreat_cost INTEGER,
            attacks TEXT,
            abilities TEXT,
            rules TEXT,
            expansion TEXT,
            number TEXT,
            rarity TEXT,
            image_url TEXT,
            source TEXT
        )
        """)
        
        conn.commit()
        conn.close()
    
    def _insert_test_data(self):
        """Insert sample card data for testing"""
        test_cards = [
            {
                'card_id': 'test-pokemon-1',
                'name': 'Test Pokemon',
                'supertype': 'Pokémon',
                'subtype': 'Basic',
                'hp': 180,
                'types': json.dumps(['Fire']),
                'retreat_cost': 2,
                'attacks': json.dumps([{
                    'name': 'Fire Blast',
                    'cost': ['Fire', 'Fire'],
                    'damage': 120,
                    'text': 'Deal 120 damage to the defending Pokémon.'
                }]),
                'abilities': json.dumps([{
                    'name': 'Draw Power',
                    'type': 'Ability',
                    'text': 'Once during your turn, you may draw 2 cards.'
                }]),
                'rules': json.dumps([]),
                'expansion': 'Test Set',
                'number': '1',
                'rarity': 'Rare',
                'image_url': '',
                'source': 'test'
            },
            {
                'card_id': 'test-trainer-1',
                'name': 'Test Supporter',
                'supertype': 'Trainer',
                'subtype': 'Supporter',
                'hp': None,
                'types': json.dumps([]),
                'retreat_cost': None,
                'attacks': json.dumps([]),
                'abilities': json.dumps([]),
                'rules': json.dumps(['Draw 3 cards.']),
                'expansion': 'Test Set',
                'number': '2',
                'rarity': 'Uncommon',
                'image_url': '',
                'source': 'test'
            }
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for card in test_cards:
            cursor.execute("""
                INSERT INTO cards VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                card['card_id'], card['name'], card['supertype'], card['subtype'],
                card['hp'], card['types'], card['retreat_cost'], card['attacks'],
                card['abilities'], card['rules'], card['expansion'], card['number'],
                card['rarity'], card['image_url'], card['source']
            ))
        
        conn.commit()
        conn.close()
    
    @patch('spacy.load')
    def test_analyzer_initialization(self, mock_spacy_load):
        """Test that CardAnalyzer initializes correctly"""
        mock_spacy_load.return_value = self.nlp_mock
        
        analyzer = CardAnalyzer(db_path=self.db_path)
        
        self.assertIsNotNone(analyzer)
        self.assertEqual(analyzer.db_path, self.db_path)
        mock_spacy_load.assert_called_once_with('en_core_web_sm')
    
    @patch('spacy.load')
    def test_card_feature_extraction(self, mock_spacy_load):
        """Test card feature extraction from database"""
        mock_spacy_load.return_value = self.nlp_mock
        
        analyzer = CardAnalyzer(db_path=self.db_path)
        features = analyzer.extract_card_features()
        
        self.assertEqual(len(features), 2)
        
        # Test Pokemon card features
        pokemon_card = next(f for f in features if f.supertype == 'Pokémon')
        self.assertEqual(pokemon_card.name, 'Test Pokemon')
        self.assertEqual(pokemon_card.hp, 180)
        self.assertEqual(pokemon_card.retreat_cost, 2)
        self.assertIn('Fire', pokemon_card.types)
        self.assertTrue(len(pokemon_card.attacks) > 0)
        self.assertTrue(len(pokemon_card.abilities) > 0)
        
        # Test Trainer card features
        trainer_card = next(f for f in features if f.supertype == 'Trainer')
        self.assertEqual(trainer_card.name, 'Test Supporter')
        self.assertEqual(trainer_card.subtype, 'Supporter')
        self.assertIsNone(trainer_card.hp)
    
    @patch('spacy.load')
    def test_role_categorization(self, mock_spacy_load):
        """Test ML-based role categorization"""
        mock_spacy_load.return_value = self.nlp_mock
        
        analyzer = CardAnalyzer(db_path=self.db_path)
        features = analyzer.extract_card_features()
        
        pokemon_card = next(f for f in features if f.supertype == 'Pokémon')
        trainer_card = next(f for f in features if f.supertype == 'Trainer')
        
        # Pokemon should have attacker roles (either main or secondary)
        attacker_roles = [role for role in pokemon_card.roles.keys() if 'attacker' in role]
        self.assertTrue(len(attacker_roles) > 0, "Pokemon should have attacker role")
        self.assertIn('draw_engine', pokemon_card.roles)
        
        # Trainer should have supporter role
        self.assertIn('draw_supporter', trainer_card.roles)
    
    @patch('spacy.load')
    def test_pros_cons_analysis(self, mock_spacy_load):
        """Test pros and cons analysis"""
        mock_spacy_load.return_value = self.nlp_mock
        
        analyzer = CardAnalyzer(db_path=self.db_path)
        features = analyzer.extract_card_features()
        
        pokemon_card = next(f for f in features if f.supertype == 'Pokémon')
        
        # Should identify HP as a strength
        hp_pros = [p for p in pokemon_card.pros if 'HP' in p]
        self.assertTrue(len(hp_pros) > 0)
        
        # Should identify retreat cost as weakness if >= 3
        if pokemon_card.retreat_cost >= 3:
            retreat_cons = [c for c in pokemon_card.cons if 'retreat' in c.lower()]
            self.assertTrue(len(retreat_cons) > 0)
    
    @patch('spacy.load')
    def test_synergy_detection(self, mock_spacy_load):
        """Test synergy detection functionality"""
        mock_spacy_load.return_value = self.nlp_mock
        
        analyzer = CardAnalyzer(db_path=self.db_path)
        features = analyzer.extract_card_features()
        
        test_decklist = {
            'Test Pokemon': 2,
            'Test Supporter': 4
        }
        
        synergy_analysis = analyzer.detect_synergies(test_decklist, features)
        
        self.assertIsInstance(synergy_analysis, SynergyAnalysis)
        self.assertIsInstance(synergy_analysis.intra_card_score, float)
        self.assertIsInstance(synergy_analysis.inter_card_synergies, list)
        self.assertIsInstance(synergy_analysis.archetype_fit, dict)
        self.assertIsInstance(synergy_analysis.recommendations, list)
    
    @patch('spacy.load')
    def test_comprehensive_report(self, mock_spacy_load):
        """Test comprehensive report generation"""
        mock_spacy_load.return_value = self.nlp_mock
        
        analyzer = CardAnalyzer(db_path=self.db_path)
        features = analyzer.extract_card_features()
        
        test_decklist = {
            'Test Pokemon': 2,
            'Test Supporter': 4
        }
        
        synergy_analysis = analyzer.detect_synergies(test_decklist, features)
        report = analyzer.generate_comprehensive_report(features, synergy_analysis)
        
        # Check report structure
        self.assertIn('summary', report)
        self.assertIn('card_analysis', report)
        self.assertIn('role_distribution', report)
        self.assertIn('synergy_report', report)
        self.assertIn('recommendations', report)
        
        # Check summary
        self.assertEqual(report['summary']['total_cards_analyzed'], 2)
        
        # Check card analysis
        self.assertEqual(len(report['card_analysis']), 2)
        
        # Check synergy report
        self.assertIn('intra_card_synergy_score', report['synergy_report'])
        self.assertIn('archetype_fit', report['synergy_report'])
    
    @patch('spacy.load')
    def test_semantic_keyword_extraction(self, mock_spacy_load):
        """Test semantic keyword extraction from card text"""
        mock_spacy_load.return_value = self.nlp_mock
        
        analyzer = CardAnalyzer(db_path=self.db_path)
        
        # Test with known patterns
        test_text = "Draw 3 cards from your deck and attach 2 energy cards"
        keywords = analyzer._extract_semantic_keywords(test_text)
        
        # Should detect draw and energy patterns
        self.assertIn('draw', keywords)
        self.assertIn('energy', keywords)
    
    @patch('spacy.load')
    def test_numerical_effects_extraction(self, mock_spacy_load):
        """Test extraction of numerical values from card effects"""
        mock_spacy_load.return_value = self.nlp_mock
        
        analyzer = CardAnalyzer(db_path=self.db_path)
        
        test_text = "Draw 3 cards and deal 120 damage"
        effects = analyzer._extract_numerical_effects(test_text)
        
        self.assertEqual(effects.get('draw_amount'), 3)
        self.assertEqual(effects.get('damage_amount'), 120)

class TestCardAnalyzerIntegration(unittest.TestCase):
    """Integration tests for CardAnalyzer with existing modules"""
    
    def test_card_recommender_integration(self):
        """Test integration with existing CardRecommender"""
        from analysis.card_recommender import CardRecommender
        
        recommender = CardRecommender()
        
        # Should be able to initialize without errors
        self.assertIsNotNone(recommender)
        
        # Test that analyzer integration doesn't break existing functionality
        test_decklist = {'Test Card': 4}
        test_errors = {'setup_missed': 5}
        
        suggestions = recommender.suggest_replacements(test_decklist, test_errors)
        
        # Should return suggestions (even if analyzer fails to initialize)
        self.assertIsInstance(suggestions, list)

if __name__ == '__main__':
    # Run tests
    unittest.main()