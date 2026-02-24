const url = "https://api.telegram.org/bot8039404178:AAH6Y6XxZtKdjUhg4ZEiCF01WH-d-7fxMxU/getMe";
const https = require("https");

console.log("Testing Node.js https module (not fetch)...");
console.log("Node version:", process.version);

const req = https.get(url, { timeout: 10000 }, (res) => {
    let data = "";
    res.on("data", (chunk) => data += chunk);
    res.on("end", () => console.log("SUCCESS:", data));
});
req.on("error", (e) => console.error("FAIL:", e.message));
req.on("timeout", () => { req.destroy(); console.error("TIMEOUT"); });
