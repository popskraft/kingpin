"""
Kingpin Game Experience Analyzer
Analyzer of game experience based on standard board game criteria
"""

import csv
import math
import statistics
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass

@dataclass
class GameMetrics:
    """Metrics for analyzing gameplay"""
    total_cards: int
    unique_abilities: int
    clans_count: int
    avg_card_complexity: float
    price_range: Tuple[int, int]
    price_variance: float
    hp_range: Tuple[int, int]
    atk_range: Tuple[int, int]
    power_variance: float
    corruption_cards_ratio: float
    defensive_cards_ratio: float
    economic_cards_ratio: float

@dataclass
class AspectScore:
    """Evaluation of a specific game aspect"""
    aspect: str
    score: float  # 1-10
    reasoning: str
    recommendations: List[str]

class GameExperienceAnalyzer:
    """Game experience analyzer for Kingpin"""
    
    def __init__(self, cards_file: str):
        self.cards = self._load_cards_from_csv(cards_file)
        self.deck_cards = [c for c in self.cards if c.get('В_колоде') == '✓']
        self.metrics = self._calculate_metrics()
    
    def _load_cards_from_csv(self, filename: str) -> List[Dict]:
        """Load cards from a CSV file"""
        cards = []
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Parse numeric values
                try:
                    card = {
                        'ID': row['ID'],
                        'Название': row['Название'],
                        'Тип': row['Тип'],
                        'Клан': row.get('Клан', row.get('Каста', '')),  # Support both headers
                        'Фракция': row['Фракция'],
                        'HP': int(row['HP']) if row['HP'].isdigit() else 0,
                        'ATK': int(row['ATK']) if row['ATK'].isdigit() else 0,
                        'Price': int(row['Price']) if row['Price'].isdigit() else 0,
                        'Corruption': int(row['Corruption']) if row['Corruption'].isdigit() else 0,
                        'Defend': int(row['Defend']) if row['Defend'].isdigit() else 0,
                        'Rage': int(row['Rage']) if row['Rage'].isdigit() else 0,
                        'ABL': row['ABL'],
                        'Independence': int(row['Independence']) if row['Independence'].isdigit() else 0,
                        'В_колоде': row['В_колоде'],
                        'Описание': row.get('Описание', '')
                    }
                    cards.append(card)
                except (ValueError, KeyError) as e:
                    print(f"Error processing card {row.get('ID', 'unknown')}: {e}")
                    continue
        return cards
    
    def _calculate_metrics(self) -> GameMetrics:
        """Compute basic game metrics"""
        if not self.deck_cards:
            return GameMetrics(0, 0, 0, 0, (0, 0), 0, (0, 0), (0, 0), 0, 0, 0, 0)
        
        # Basic characteristics
        total_cards = len(self.deck_cards)
        unique_abilities = len(set(c['ABL'] for c in self.deck_cards if c['ABL'] and c['ABL'].strip()))
        clans = set(c['Клан'] for c in self.deck_cards if c['Клан'])
        clans_count = len(clans)
        
        # Card text complexity (number of words in abilities)
        complexity_scores = []
        for card in self.deck_cards:
            if card['ABL'] and card['ABL'].strip():
                complexity_scores.append(len(card['ABL'].split()))
            else:
                complexity_scores.append(0)
        avg_card_complexity = statistics.mean(complexity_scores) if complexity_scores else 0
        
        # Economy indicators
        prices = [c['Price'] for c in self.deck_cards]
        price_range = (min(prices), max(prices)) if prices else (0, 0)
        price_variance = statistics.variance(prices) if len(prices) > 1 else 0
        
        # Combat indicators
        hps = [c['HP'] for c in self.deck_cards]
        atks = [c['ATK'] for c in self.deck_cards]
        hp_range = (min(hps), max(hps)) if hps else (0, 0)
        atk_range = (min(atks), max(atks)) if atks else (0, 0)
        
        # Power variance (HP + ATK)
        power_values = [c['HP'] + c['ATK'] for c in self.deck_cards]
        power_variance = statistics.variance(power_values) if len(power_values) > 1 else 0
        
        # Special mechanics
        corruption_cards = sum(1 for c in self.deck_cards if c['Corruption'] > 0)
        defensive_cards = sum(1 for c in self.deck_cards if c['Defend'] > 0)
        economic_cards = sum(1 for c in self.deck_cards 
                           if c['ABL'] and any(keyword in c['ABL'].lower() 
                                          for keyword in ['economy', 'steal', 'gain', 'audit', 'экономика']))
        
        corruption_ratio = corruption_cards / total_cards if total_cards > 0 else 0
        defensive_ratio = defensive_cards / total_cards if total_cards > 0 else 0
        economic_ratio = economic_cards / total_cards if total_cards > 0 else 0
        
        return GameMetrics(
            total_cards=total_cards,
            unique_abilities=unique_abilities,
            clans_count=clans_count,
            avg_card_complexity=avg_card_complexity,
            price_range=price_range,
            price_variance=price_variance,
            hp_range=hp_range,
            atk_range=atk_range,
            power_variance=power_variance,
            corruption_cards_ratio=corruption_ratio,
            defensive_cards_ratio=defensive_ratio,
            economic_cards_ratio=economic_ratio
        )
    
    def analyze_learning_ease(self) -> AspectScore:
        """Analyze ease of learning (1-10)"""
        score = 10.0
        reasoning_parts = []
        recommendations = []
        
        # Number of unique mechanics (more = harder)
        if self.metrics.unique_abilities > 20:
            score -= 2.0
            reasoning_parts.append("many unique abilities")
            recommendations.append("Simplify or merge similar abilities")
        elif self.metrics.unique_abilities > 15:
            score -= 1.0
            reasoning_parts.append("moderate number of abilities")
        
        # Ability text complexity
        if self.metrics.avg_card_complexity > 8:
            score -= 2.0
            reasoning_parts.append("complex ability descriptions")
            recommendations.append("Shorten ability text, use icons")
        elif self.metrics.avg_card_complexity > 5:
            score -= 1.0
            reasoning_parts.append("medium text complexity")
        
        # Number of clans (more choice = harder)
        if self.metrics.clans_count > 6:
            score -= 1.5
            reasoning_parts.append("many clans to learn")
            recommendations.append("Consider a base set with fewer clans")
        elif self.metrics.clans_count < 3:
            score -= 1.0
            reasoning_parts.append("low clan variety")
            recommendations.append("Add more clans for diversity")
        
        # Price variance (economy predictability)
        if self.metrics.price_variance > 2.0:
            score -= 1.0
            reasoning_parts.append("unpredictable economy")
            recommendations.append("Make pricing more logical")
        
        reasoning = f"Ease of learning: {', '.join(reasoning_parts)}"
        
        return AspectScore(
            aspect="Ease of learning",
            score=max(1.0, min(10.0, score)),
            reasoning=reasoning,
            recommendations=recommendations
        )
    
    def analyze_excitement(self) -> AspectScore:
        """Analyze excitement/thrill (1-10)"""
        score = 5.0
        reasoning_parts = []
        recommendations = []
        
        # Power variance of cards (creates tension)
        if self.metrics.power_variance > 10:
            score += 2.0
            reasoning_parts.append("high variance in card power")
        elif self.metrics.power_variance > 5:
            score += 1.0
            reasoning_parts.append("moderate variance")
        else:
            score -= 1.0
            reasoning_parts.append("low power variance")
            recommendations.append("Add more diversity in card power")
        
        # Interaction mechanics (corruption, steal, etc.)
        interaction_score = (self.metrics.corruption_cards_ratio + 
                           self.metrics.economic_cards_ratio) * 10
        if interaction_score > 4:
            score += 2.0
            reasoning_parts.append("many interactive mechanics")
        elif interaction_score > 2:
            score += 1.0
            reasoning_parts.append("moderate interaction")
        else:
            score -= 1.0
            reasoning_parts.append("little interaction between players")
            recommendations.append("Add more cards with interactive abilities")
        
        # Defensive mechanics (add tactical depth)
        if self.metrics.defensive_cards_ratio > 0.3:
            score += 1.0
            reasoning_parts.append("good defensive tactics")
        elif self.metrics.defensive_cards_ratio < 0.1:
            score -= 1.0
            reasoning_parts.append("few defensive options")
            recommendations.append("Add more defensive mechanics")
        
        # Clan diversity
        if self.metrics.clans_count >= 4:
            score += 1.0
            reasoning_parts.append("good diversity of clans")
        else:
            recommendations.append("Increase the number of unique clans")
        
        reasoning = f"Excitement/Thrill: {', '.join(reasoning_parts)}"
        
        return AspectScore(
            aspect="Excitement/Thrill",
            score=max(1.0, min(10.0, score)),
            reasoning=reasoning,
            recommendations=recommendations
        )
    
    def analyze_strategic_depth(self) -> AspectScore:
        """Analyze strategic depth (1-10)"""
        score = 5.0
        reasoning_parts = []
        recommendations = []
        
        # Number of unique strategies (clans × abilities)
        strategic_combinations = self.metrics.clans_count * (self.metrics.unique_abilities / 5)
        if strategic_combinations > 20:
            score += 2.5
            reasoning_parts.append("many strategic combinations")
        elif strategic_combinations > 10:
            score += 1.5
            reasoning_parts.append("good variety of strategies")
        else:
            score -= 1.0
            reasoning_parts.append("limited strategic options")
            recommendations.append("Increase synergies between cards and clans")
        
        # Economic complexity
        if self.metrics.economic_cards_ratio > 0.2:
            score += 1.5
            reasoning_parts.append("complex economic gameplay")
        elif self.metrics.economic_cards_ratio > 0.1:
            score += 0.5
            reasoning_parts.append("basic economy")
        else:
            recommendations.append("Add more economic decision-making")
        
        # Price range (bigger range = more decisions)
        price_range_size = self.metrics.price_range[1] - self.metrics.price_range[0]
        if price_range_size > 4:
            score += 1.0
            reasoning_parts.append("wide range of card costs")
        elif price_range_size < 2:
            score -= 1.0
            recommendations.append("Increase the range of card costs")
        
        reasoning = f"Strategic depth: {', '.join(reasoning_parts)}"
        
        return AspectScore(
            aspect="Strategic depth",
            score=max(1.0, min(10.0, score)),
            reasoning=reasoning,
            recommendations=recommendations
        )
    
    def analyze_replayability(self) -> AspectScore:
        """Analyze replayability (1-10)"""
        score = 5.0
        reasoning_parts = []
        recommendations = []
        
        # Number of cards per clan (more = more deckbuilding options)
        avg_cards_per_clan = self.metrics.total_cards / max(1, self.metrics.clans_count)
        if avg_cards_per_clan > 15:
            score += 2.0
            reasoning_parts.append("many cards for each clan")
        elif avg_cards_per_clan > 10:
            score += 1.0
            reasoning_parts.append("enough cards for variety")
        else:
            score -= 1.0
            reasoning_parts.append("few cards per clan")
            recommendations.append("Add more cards for each clan")
        
        # Clan uniqueness
        if self.metrics.clans_count >= 4:
            score += 1.5
            reasoning_parts.append("many unique clans")
        elif self.metrics.clans_count >= 3:
            score += 0.5
            reasoning_parts.append("basic diversity of clans")
        
        # Ability combinatorics
        ability_combinations = self.metrics.unique_abilities * self.metrics.clans_count
        if ability_combinations > 80:
            score += 1.5
            reasoning_parts.append("high ability combinatorics")
        elif ability_combinations > 40:
            score += 0.5
            reasoning_parts.append("moderate combinatorics")
        
        reasoning = f"Replayability: {', '.join(reasoning_parts)}"
        
        return AspectScore(
            aspect="Replayability",
            score=max(1.0, min(10.0, score)),
            reasoning=reasoning,
            recommendations=recommendations
        )
    
    def analyze_balance(self) -> AspectScore:
        """Analyze balance (1-10)"""
        score = 8.0  # Start from a good balance
        reasoning_parts = []
        recommendations = []
        
        # Power variance (too large = imbalance)
        if self.metrics.power_variance > 15:
            score -= 3.0
            reasoning_parts.append("large spread in card power")
            recommendations.append("Even out card power or add compensating mechanics")
        elif self.metrics.power_variance > 8:
            score -= 1.5
            reasoning_parts.append("moderate spread of power")
        else:
            reasoning_parts.append("well-balanced card power")
        
        # Price variance
        if self.metrics.price_variance > 3:
            score -= 1.5
            reasoning_parts.append("uneven pricing")
            recommendations.append("Revisit card costs relative to their power")
        
        # Distribution of special mechanics
        total_special = (self.metrics.corruption_cards_ratio + 
                        self.metrics.defensive_cards_ratio + 
                        self.metrics.economic_cards_ratio)
        if total_special > 0.8:
            score -= 1.0
            reasoning_parts.append("too many special mechanics")
            recommendations.append("Add more simple cards for balance")
        elif total_special < 0.3:
            score -= 1.0
            reasoning_parts.append("too few special mechanics")
            recommendations.append("Add more unique abilities")
        
        reasoning = f"Balance: {', '.join(reasoning_parts)}"
        
        return AspectScore(
            aspect="Balance",
            score=max(1.0, min(10.0, score)),
            reasoning=reasoning,
            recommendations=recommendations
        )
    
    def generate_comprehensive_report(self) -> str:
        """Generate a comprehensive game experience analysis report"""
        aspects = {
            "learning_ease": self.analyze_learning_ease(),
            "excitement": self.analyze_excitement(),
            "strategic_depth": self.analyze_strategic_depth(),
            "replayability": self.analyze_replayability(),
            "balance": self.analyze_balance()
        }
        
        report = "# KINGPIN GAME EXPERIENCE ANALYSIS\n\n"
        
        # General metrics
        report += "## General game characteristics\n\n"
        report += f"- **Total cards in decks**: {self.metrics.total_cards}\n"
        report += f"- **Number of clans**: {self.metrics.clans_count}\n"
        report += f"- **Unique abilities**: {self.metrics.unique_abilities}\n"
        report += f"- **Price range**: {self.metrics.price_range[0]}-{self.metrics.price_range[1]}💰\n"
        report += f"- **HP range**: {self.metrics.hp_range[0]}-{self.metrics.hp_range[1]}\n"
        report += f"- **ATK range**: {self.metrics.atk_range[0]}-{self.metrics.atk_range[1]}\n"
        report += f"- **Cards with corruption**: {self.metrics.corruption_cards_ratio:.1%}\n"
        report += f"- **Defensive cards**: {self.metrics.defensive_cards_ratio:.1%}\n"
        report += f"- **Economic cards**: {self.metrics.economic_cards_ratio:.1%}\n\n"
        
        # Aspect scores
        report += "## Game experience assessment\n\n"
        
        total_score = 0
        for aspect_key, score in aspects.items():
            total_score += score.score
            
            # Emoji for score band
            if score.score >= 8:
                emoji = "🟢"
            elif score.score >= 6:
                emoji = "🟡"
            else:
                emoji = "🔴"
            
            report += f"### {emoji} {score.aspect}: {score.score:.1f}/10\n"
            report += f"**Analysis**: {score.reasoning}\n\n"
            
            if score.recommendations:
                report += "**Recommendations**:\n"
                for rec in score.recommendations:
                    report += f"- {rec}\n"
                report += "\n"
        
        # Overall score
        avg_score = total_score / len(aspects)
        report += f"## Overall score: {avg_score:.1f}/10\n\n"
        
        if avg_score >= 8:
            report += "🎉 **EXCELLENT GAME** - high-quality game experience\n"
        elif avg_score >= 6:
            report += "👍 **GOOD GAME** - solid experience with room for improvement\n"
        elif avg_score >= 4:
            report += "⚠️ **NEEDS IMPROVEMENT** - significant issues to address\n"
        else:
            report += "🔴 **CRITICAL ISSUES** - major overhaul required\n"
        
        # Priority recommendations
        all_recommendations = []
        for aspect in aspects.values():
            all_recommendations.extend(aspect.recommendations)
        
        if all_recommendations:
            report += "\n## Priority improvement recommendations\n\n"
            for i, rec in enumerate(all_recommendations[:5], 1):
                report += f"{i}. {rec}\n"
        
        return report

def main():
    """Run game experience analysis"""
    analyzer = GameExperienceAnalyzer("config/cards.csv")
    report = analyzer.generate_comprehensive_report()
    
    # Save report
    with open("docs/game_experience_analysis.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print("📊 Game experience analysis complete!")
    print("📄 Report saved to docs/game_experience_analysis.md")
    print(f"\n{report}")

if __name__ == "__main__":
    main()
