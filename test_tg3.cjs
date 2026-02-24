const dns = require("dns");
dns.setDefaultResultOrder("ipv4first");

const url = "https://api.telegram.org/bot8039404178:AAH6Y6XxZtKdjUhg4ZEiCF01WH-d-7fxMxU/getMe";

console.log("Test 1: Node.js https with IPv4 forced...");
const https = require("https");
const req = https.get(url, { family: 4, timeout: 10000 }, (res) => {
    let data = "";
    res.on("data", (chunk) => data += chunk);
    res.on("end", () => {
        console.log("SUCCESS:", data.substring(0, 100));
        process.exit(0);
    });
});
req.on("error", (e) => { console.error("FAIL:", e.message, e.code); process.exit(1); });
req.on("timeout", () => { req.destroy(); console.error("TIMEOUT"); process.exit(1); });
