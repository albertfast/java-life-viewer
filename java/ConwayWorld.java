import java.util.ArrayList;
import java.util.List;

public class ConwayWorld {

  private int rowCount;
  private int colCount;

  private Cell[][] grid = new Cell[rowCount][colCount];
  private List<Cell> replacementCellsInNextGeneration;

  public ConwayWorld() {
    this(15, 20);
  }

  public ConwayWorld(int rowCount, int colCount) {
    this.rowCount = rowCount;
    this.colCount = colCount;

    this.grid = new Cell[rowCount][colCount];
    this.replacementCellsInNextGeneration = new ArrayList<Cell>();

    for (int r = 0; r < rowCount; r++) {
      for (int c = 0; c < colCount; c++) {
        grid[r][c] = new ConwayCell(r, c, this);
      }
    }
  }

  // Create a string that displays the grid
  public String displayString() {
    String displayString = "";

    for (int r = 0; r < rowCount; r++) {
      for (int c = 0; c < colCount; c++) {
        displayString += " " + grid[r][c].displayCharacter();
      }

      displayString += "\n";
    }

    return displayString;
  }
  
  public void replaceCell(Cell cell) {
    grid[cell.getRow()][cell.getColumn()] = cell;
  }

  // Create the next generation
  public void advanceToNextGeneration() {
    Cell[][] nextGrid = new Cell[rowCount][colCount];

    // Build the grid for the next generation
    for (int r = 0; r < rowCount; r++) {
      for (int c = 0; c < colCount; c++) {
        nextGrid[r][c] = grid[r][c].cellForNextGeneration();
      }
    }

    // Out with the old, in with the new
    grid = nextGrid;
 }

  // Returns true if (r, c) is a valid coordinate, and the cell is alive
  public boolean isAlive(int r, int c) {
    return r >= 0 && c >= 0 && r < rowCount && c < colCount && grid[r][c].getIsAlive();
  }

  // Returns the number of neighbors of the cell at (r, c)
  public int neighborCount(int r, int c) {
    int count = 0;

    // the row above
    if (this.isAlive(r - 1, c - 1))
      count++;
    if (this.isAlive(r - 1, c))
      count++;
    if (this.isAlive(r - 1, c + 1))
      count++;

    // Same row as this cell
    if (this.isAlive(r, c - 1))
      count++;
    if (this.isAlive(r, c + 1))
      count++;

    // The row below
    if (this.isAlive(r + 1, c - 1))
      count++;
    if (this.isAlive(r + 1, c))
      count++;
    if (this.isAlive(r + 1, c + 1))
      count++;

    return count;
  }

  public int otherNeighborCount(int row, int col) {
    int count = 0;

    // loop through row above, current row, and row after
    for (int r = row - 1; r <= row + 1; r++) {

      // column to left, current column, column to right
      for (int c = col - 1; r<= col + 1; c++) {
        if (isAlive(r, c)) {
          count++;
        }
      }
    }

    // subtract out the cell, it is not neighbor
    if (isAlive(row, col)) {
      count--;
    }

    return count;
  }

  public int getRowCount() {
    return rowCount;
  }

  public int getColumnCount() {
    return colCount;
  }
}