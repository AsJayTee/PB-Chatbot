import logging
from main import main

logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s - %(levelname)s - %(message)s')
app = main(debug = True)
while (query := input("Input: ")):
    print(app.chat(query))
cost = app.get_new_costs()
print(f"Embedding Cost: {(embed_cost := cost.get('embed_cost'))}")
print(f"GPT-4o Cost: {(gpt_4o_cost := cost.get('gpt_4o_cost'))}")
print(f"GPT-4o-mini Cost: {(gpt_4o_mini_cost := cost.get('gpt_4o_mini_cost'))}")
print(f"Total Cost: {embed_cost + gpt_4o_cost + gpt_4o_mini_cost}")