class BaseGenerator:
    """Base class for AI question generators.
    
    This abstract class defines the interface that all question generators must implement.
    """
    def generate_question(self, context: str) -> str:
        """Generate a question based on the given context.
        
        Args:
            context: The context to generate a question from.
            
        Returns:
            A generated question as a string.
            
        Raises:
            NotImplementedError: If the method is not implemented by a subclass.
        """
        raise NotImplementedError("Subclasses must implement `generate_question`")
