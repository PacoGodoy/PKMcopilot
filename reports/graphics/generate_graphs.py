import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

DETAILS_CSV = "reports/detail_player_01.csv"

def winrate_by_deck():
    df = pd.read_csv(DETAILS_CSV)
    winrates = df.groupby('player_deck')['result'].apply(lambda r: (r == "Win").mean())
    winrates.plot(kind="bar", title="Winrate by Deck")
    plt.ylabel("Winrate")
    plt.savefig("reports/graphics/winrate_by_deck.png")
    plt.clf()

def phase_performance():
    df = pd.read_csv(DETAILS_CSV)
    phase_cols = ["start", "mid", "end"]
    phase_map = {"good": 2, "avg": 1, "average": 1, "bad": 0, "needs work": 0}
    for phase in phase_cols:
        df[phase] = df["phase_performance"].str.extract(f"{phase}:([a-zA-Z ]+);?")
        df[phase] = df[phase].map(lambda v: phase_map.get(str(v).lower().strip(), None))
    df[phase_cols].mean().plot(kind="bar", title="Average Phase Performance (2=good, 1=avg, 0=bad)")
    plt.ylabel("Performance")
    plt.savefig("reports/graphics/phase_performance.png")
    plt.clf()

def common_errors():
    df = pd.read_csv(DETAILS_CSV)
    errors = df["errors"].dropna().str.split(";|,").explode().str.strip()
    errors.value_counts().plot(kind="bar", title="Common Errors")
    plt.ylabel("Count")
    plt.savefig("reports/graphics/common_errors.png")
    plt.clf()

def matchup_heatmap():
    df = pd.read_csv(DETAILS_CSV)
    matrix = pd.pivot_table(df, values="result", index="player_deck", columns="opponent_deck",
                            aggfunc=lambda r: (r == "Win").mean())
    sns.heatmap(matrix, annot=True, cmap="Blues")
    plt.title("Matchup Winrate Heatmap")
    plt.savefig("reports/graphics/matchup_heatmap.png")
    plt.clf()

def style_distribution():
    # Example: Assume playstyle tagged in summary (expand as needed)
    styles = ["Aggro", "Toolbox", "Control"]
    counts = [5, 3, 2]  # Example data
    plt.pie(counts, labels=styles, autopct="%1.0f%%")
    plt.title("Playstyle Distribution")
    plt.savefig("reports/graphics/style_distribution.png")
    plt.clf()

if __name__ == "__main__":
    winrate_by_deck()
    phase_performance()
    common_errors()
    matchup_heatmap()
    style_distribution()