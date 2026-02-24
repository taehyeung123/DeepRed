const url = "https://api.telegram.org/bot8039404178:AAH6Y6XxZtKdjUhg4ZEiCF01WH-d-7fxMxU/getMe";

console.log("Testing Node.js fetch to Telegram API...");
console.log("Node version:", process.version);

try {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10000);
  const res = await fetch(url, { signal: controller.signal });
  clearTimeout(timeout);
  const data = await res.json();
  console.log("SUCCESS:", JSON.stringify(data));
} catch (e) {
  console.error("FAIL:", e.message);
  console.error("Type:", e.constructor.name);
}
