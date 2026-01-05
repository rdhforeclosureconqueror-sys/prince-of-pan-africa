// ✅ src/routes/adminHolisticRoutes.js
import { Router } from "express";
import { pool } from "../server.js";
const r = Router();

r.get("/overview", async (_req, res) => {
  const data = await pool.query(`SELECT * FROM ai_holistic_state ORDER BY overall_health DESC`);
  res.json({ ok: true, holistic: data.rows });
});

export default r;
