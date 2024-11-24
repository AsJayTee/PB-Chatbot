from systems.model.model import ChatModel, EmbeddingModel

class CostTracker:
    chat_model : ChatModel
    embedding_model : EmbeddingModel
    embed_cost : float = 0
    gpt_4o_cost : float = 0
    gpt_4o_mini_cost : float = 0

    def __init__(
            self, 
            chat_model : ChatModel, 
            embedding_model : EmbeddingModel
            ) -> None:
        self.chat_model = chat_model
        self.embedding_model = embedding_model
    
    def update_costs(self) -> dict[str : float]:
        embed_cost, embed_diff = self.__get_embedding_costs()
        gpt_4o_cost, gpt_4o_diff, gpt_4o_mini_cost, gpt_4o_mini_diff = \
        self.__get_gpt_costs()
        return {
            "embed_cost" : embed_cost,
            "embed_diff" : embed_diff,
            "gpt_4o_cost" : gpt_4o_cost,
            "gpt_4o_diff" : gpt_4o_diff,
            "gpt_4o_mini_cost" : gpt_4o_mini_cost,
            "gpt_4o_mini_diff" : gpt_4o_mini_diff
        }
    
    def __get_embedding_costs(self) -> tuple[float]:
        new_embed_cost = self.embedding_model.get_cost()
        embed_diff = new_embed_cost - self.embed_cost
        self.embed_cost = new_embed_cost
        return new_embed_cost, embed_diff
    
    def __get_gpt_costs(self) -> tuple[float]:
        new_costs = self.chat_model.get_cost()

        new_gpt_4o_cost = new_costs.get("in-gpt-4o") + \
        new_costs.get("out-gpt-4o")

        gpt_4o_diff = new_gpt_4o_cost - self.gpt_4o_cost
        self.gpt_4o_cost = new_gpt_4o_cost

        new_gpt_4o_mini_cost = new_costs.get("in-gpt-4o-mini") + \
        new_costs.get("out-gpt-4o-mini")

        gpt_4o_mini_diff = new_gpt_4o_mini_cost - self.gpt_4o_mini_cost
        self.gpt_4o_mini_cost = new_gpt_4o_mini_cost

        return new_gpt_4o_cost, gpt_4o_diff, new_gpt_4o_mini_cost, gpt_4o_mini_diff
