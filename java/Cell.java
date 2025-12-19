public interface Cell {
  char displayCharacter();
  Cell cellForNextGeneration();
  
  void setIsAlive(boolean value); 
  boolean getIsAlive();
  
  int getRow(); 
  int getColumn();
}