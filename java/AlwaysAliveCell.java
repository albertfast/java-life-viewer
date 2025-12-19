
public class AlwaysAliveCell extends AbstractCell {
	
	public AlwaysAliveCell(int r, int c, ConwayWorld w) {
		super(r, c, w);
	}
	
	public  AbstractCell cellForNextGeneration() {
		return this;
	}
	
	public boolean willBeAliveInNextGeneration() {
		return true;
	}
	
	public boolean getIsAlive() {
		return true;
	}
	
	public char displayCharacter() {
		return '+';
	}
}