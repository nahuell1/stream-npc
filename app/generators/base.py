class BaseGenerator:
    def generate_question(self, context: str) -> str:
        raise NotImplementedError("Debes implementar `generate_question`")
