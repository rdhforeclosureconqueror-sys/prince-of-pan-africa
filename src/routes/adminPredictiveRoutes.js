// ✅ src/routes/adminPredictiveRoutes.js
import { Router } from "express";
import { pool } from "../server.js";

const r = Router();

r.get("/predictions", async (_req, res) => {
  const data = await pool.query(`
    SELECT p.*, m.display_name
    FROM ai_predictions p
    JOIN members m ON m.member_id = p.member_id
    ORDER BY p.created_at DESC LIMIT 50
  `);
  res.json({ ok: true, predictions: data.rows });
});

export default r;
