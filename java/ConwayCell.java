
public class ConwayCell extends AbstractCell {

	public ConwayCell(int r, int c, ConwayWorld w) {
		super(r, c, w);
	}	

  /**
   * These are the Conway Game of Life Rules
   */
	private boolean willBeAliveInNextGeneration() {
		int nc = world.neighborCount(getRow(), getColumn());
		
		if (getIsAlive()) {
			return nc == 2 || nc == 3;
		} else {
			return nc == 3;
		}
	}
	
	public AbstractCell cellForNextGeneration() {
		ConwayCell next = new ConwayCell(getRow(), getColumn(), world);
		
		next.setIsAlive(willBeAliveInNextGeneration());
		
		return next;
	}	
}