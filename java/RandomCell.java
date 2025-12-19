/**
 * Custom Cell: This cell has a 50% chance to be alive
 * in every new generation regardless of neighbors.
 */
public class RandomCell extends AbstractCell {

    public RandomCell(int r, int c, ConwayWorld w) {
        super(r, c, w);
    }

    @Override
    public Cell cellForNextGeneration() {
        RandomCell next = new RandomCell(getRow(), getColumn(), world);
        // Randomly set alive or dead (50/50 chance)
        next.setIsAlive(Math.random() > 0.5);
        return next;
    }

    @Override
    public char displayCharacter() {
        // 'R' stands for Random
        return isAlive ? 'R' : '.';
    }
}