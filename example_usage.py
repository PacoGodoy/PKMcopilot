#!/usr/bin/env python
"""
example_usage.py - Demonstration of the comprehensive CardAnalyzer functionality

This script demonstrates how to use the CardAnalyzer module for comprehensive
Pokemon TCG card analysis, including feature extraction, role categorization,
synergy detection, and deck recommendations.
"""

import sys
import os
import json

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analysis.card_analyzer import CardAnalyzer
from analysis.card_recommender import CardRecommender

def demonstrate_card_analysis():
    """Demonstrate comprehensive card analysis capabilities"""
    
    print("=== Pokemon TCG Card Analyzer Demonstration ===\n")
    
    try:
        # Initialize the analyzer
        print("1. Initializing CardAnalyzer...")
        analyzer = CardAnalyzer()
        
        # Extract and analyze all cards
        print("2. Extracting card features from database...")
        card_features = analyzer.extract_card_features()
        
        if not card_features:
            print("   Warning: No cards found in database!")
            print("   Please populate the database with card data first.")
            return
            
        print(f"   Found {len(card_features)} cards in database")
        
        # Display individual card analysis
        print("\n3. Individual Card Analysis:")
        print("-" * 50)
        
        for card in card_features[:3]:  # Show first 3 cards
            print(f"\n📱 {card.name}")
            print(f"   Type: {card.supertype} - {card.subtype}")
            if card.hp:
                print(f"   HP: {card.hp}")
            if card.retreat_cost is not None:
                print(f"   Retreat Cost: {card.retreat_cost}")
            
            # Show top roles
            if card.roles:
                top_roles = sorted(card.roles.items(), key=lambda x: x[1], reverse=True)[:3]
                print(f"   🎯 Primary Roles: {', '.join([f'{role} ({conf:.1%})' for role, conf in top_roles])}")
            
            # Show pros and cons
            if card.pros:
                print(f"   ✅ Pros: {', '.join(card.pros[:2])}")
            if card.cons:
                print(f"   ❌ Cons: {', '.join(card.cons[:2])}")
                
            # Show semantic keywords
            if card.semantic_keywords:
                print(f"   🔑 Keywords: {', '.join(card.semantic_keywords[:5])}")
        
        # Demonstrate synergy analysis
        print("\n4. Synergy Analysis:")
        print("-" * 50)
        
        # Example decklist
        example_decklist = {
            "Charizard ex": 2,
            "Professor's Research": 4,
            "Fire Energy": 8
        }
        
        print(f"   Analyzing decklist: {example_decklist}")
        
        synergy_analysis = analyzer.detect_synergies(example_decklist, card_features)
        
        print(f"   📊 Intra-card synergy score: {synergy_analysis.intra_card_score:.3f}")
        
        # Show archetype fit
        print(f"   🎪 Archetype Analysis:")
        sorted_archetypes = sorted(synergy_analysis.archetype_fit.items(), 
                                 key=lambda x: x[1], reverse=True)
        for archetype, score in sorted_archetypes[:3]:
            print(f"      {archetype.title()}: {score:.1%}")
        
        # Show top synergies
        if synergy_analysis.inter_card_synergies:
            print(f"   🔗 Top Card Synergies:")
            for card1, card2, score in synergy_analysis.inter_card_synergies[:3]:
                print(f"      {card1} + {card2}: {score:.3f}")
        
        # Show recommendations
        print(f"   💡 Recommendations ({len(synergy_analysis.recommendations)}):")
        for rec in synergy_analysis.recommendations[:3]:
            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
            emoji = priority_emoji.get(rec.get('priority', 'low'), "⚪")
            print(f"      {emoji} {rec['suggestion']}")
            print(f"         Reason: {rec['reason']}")
        
        # Generate comprehensive report
        print("\n5. Comprehensive Report Generation:")
        print("-" * 50)
        
        report = analyzer.generate_comprehensive_report(card_features, synergy_analysis)
        
        print(f"   📋 Report Summary:")
        print(f"      Cards analyzed: {report['summary']['total_cards_analyzed']}")
        print(f"      Analysis timestamp: {report['summary']['analysis_timestamp']}")
        
        print(f"   📈 Role Distribution:")
        for role, count in sorted(report['role_distribution'].items(), 
                                key=lambda x: x[1], reverse=True)[:5]:
            print(f"      {role.replace('_', ' ').title()}: {count}")
        
        # Demonstrate integration with CardRecommender
        print("\n6. Enhanced Card Recommendation:")
        print("-" * 50)
        
        recommender = CardRecommender()
        
        # Example error statistics from gameplay
        error_stats = {
            'setup_missed': 4,
            'resource_starved': 2,
            'dead_cards': {'Fire Energy': 3}
        }
        
        print(f"   Input error stats: {error_stats}")
        suggestions = recommender.suggest_replacements(example_decklist, error_stats)
        
        print(f"   💭 Generated {len(suggestions)} suggestions:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"      {i}. {suggestion['out']} → {suggestion['in']}")
            print(f"         {suggestion['reason']}")
        
        print("\n🎉 Demonstration completed successfully!")
        print("\nThe CardAnalyzer provides comprehensive analysis including:")
        print("• Feature extraction from database")
        print("• NLP-based semantic keyword analysis")
        print("• ML-based role categorization with confidence scores")
        print("• Automated pros/cons identification")
        print("• Intra-card and inter-card synergy detection")
        print("• Archetype evaluation and recommendations")
        print("• Integration with existing analysis modules")
        
    except Exception as e:
        print(f"❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    demonstrate_card_analysis()