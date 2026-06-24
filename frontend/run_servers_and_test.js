const puppeteer = require('puppeteer');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

async function main() {
  console.log("Starting backend...");
  const backend = spawn('python', ['-m', 'uvicorn', 'app.main:app', '--port', '8000'], {
    cwd: path.resolve(__dirname, '../backend'),
  });

  console.log("Starting frontend...");
  const frontend = spawn('npm', ['run', 'dev'], {
    cwd: path.resolve(__dirname),
  });

  await new Promise(r => setTimeout(r, 5000)); // wait for servers to start

  console.log("Servers started. Launching Puppeteer...");
  const browser = await puppeteer.launch({ headless: "new", args: ['--no-sandbox'] });
  const page = await browser.newPage();

  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('BROWSER CONSOLE ERROR:', msg.text());
    }
  });
  page.on('pageerror', error => {
    console.log('BROWSER PAGE ERROR:', error.message);
  });

  await page.setRequestInterception(true);
  page.on('request', request => {
    if (request.url().includes('/practice/') && request.url().includes('/batch')) {
      const brokenProblem = fs.readFileSync(path.resolve(__dirname, '../local_only/scratch/broken_problem.json'), 'utf8');
      request.respond({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ problems: [JSON.parse(brokenProblem)] })
      });
    } else {
      request.continue();
    }
  });

  try {
    await page.goto('http://localhost:5173');
    await new Promise(r => setTimeout(r, 2000));

    // Wait for the UI. We need to bypass login or create a user.
    // The UI might have a "Register New Student" button or we can inject state.
    // Actually, instead of clicking through, we can evaluate a script to set localStorage and reload?
    // Let's just click "Register New Student", "Test", "1234"
    console.log("Clicking around to trigger the problem...");
    // Just find any way to get to PracticeView.
  } catch (err) {
    console.error("Script error:", err);
  } finally {
    await browser.close();
    backend.kill();
    frontend.kill();
  }
}
main();
