import java.util.Scanner;

class Main {

	public static void main(String[] args) throws InterruptedException {
		ConwayWorld world = new ConwayWorld();

		// Add some live conway cells, in a horizontal line
		for (int i = 0; i < 8; i++) {
			ConwayCell c = new ConwayCell(5, 5 + i, world);
			c.setIsAlive(true);
			world.replaceCell(c);
		}

		// 1. Add an AlternatingCell at (2, 2) [cite: 24, 25]
        // This fulfills the requirement to have a cell that toggles state every generation
		AlternatingCell ac = new AlternatingCell(2, 2, world);
        ac.setIsAlive(true);
        world.replaceCell(ac);

		// 2. Add a RandomCell at (8, 8) [cite: 32]
        // This is my custom cell that ignores neighbors and acts randomly [cite: 28]
        RandomCell rc = new RandomCell(8, 8, world);
        rc.setIsAlive(true);
        world.replaceCell(rc);

        // Add a Glider pattern (a moving spaceship)
		int startR = 1, startC = 1;
		int[][] gliderCoords = {{0,1}, {1,2}, {2,0}, {2,1}, {2,2}};
		for (int[] coord : gliderCoords) {
			ConwayCell c = new ConwayCell(startR + coord[0], startC + coord[1], world);
			c.setIsAlive(true);
			world.replaceCell(c);
		}

		// Add an always-alive cell
		AbstractCell a = new AlwaysAliveCell(12, 12, world);
		world.replaceCell(a);

		// Add an never-alive cell
		AbstractCell n = new NeverAliveCell(10, 10, world);
		world.replaceCell(n);

		// Go!
		while (true) {
      clearConsole();
			System.out.println(world.displayString());
			world.advanceToNextGeneration();
			Thread.sleep(500);
		}
	}

  public static void clearConsole() {
    // This crazy looking string clears the console.
    System.out.print("\033[H\033[2J");
    System.out.flush();
  }
}
