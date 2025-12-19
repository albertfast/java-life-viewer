public class AlternatingCell extends AbstractCell {

    public AlternatingCell(int r, int c, ConwayWorld w) {
        super(r, c, w);
    }

    @Override
    public Cell cellForNextGeneration() {
        AlternatingCell next = new AlternatingCell(getRow(), getColumn(), world);
        // Switch state: if alive -> dead, if dead -> alive
        next.setIsAlive(!this.getIsAlive());
        return next;
    }

    @Override
    public char displayCharacter() {
        // Show 'A' for Alternating when it is alive
        return isAlive ? 'A' : '.';
    }
}