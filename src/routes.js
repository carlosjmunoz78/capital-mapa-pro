import express from "express";
import { query } from "./db.js";

export const router = express.Router();

router.get("/health", (_req, res) => {
  res.json({ status: "ok" });
});

router.get("/countries", async (_req, res, next) => {
  try {
    const result = await query(
      "select id, name, iso_code, region, population from countries order by name"
    );
    res.json(result.rows);
  } catch (error) {
    next(error);
  }
});

router.get("/capitals", async (_req, res, next) => {
  try {
    const result = await query(
      "select capitals.id, capitals.name, countries.name as country, capitals.latitude, capitals.longitude from capitals join countries on capitals.country_id = countries.id order by capitals.name"
    );
    res.json(result.rows);
  } catch (error) {
    next(error);
  }
});

router.get("/capitals/:id", async (req, res, next) => {
  try {
    const result = await query(
      "select capitals.id, capitals.name, capitals.latitude, capitals.longitude, capitals.population, capitals.timezone, countries.name as country from capitals join countries on capitals.country_id = countries.id where capitals.id = $1",
      [req.params.id]
    );

    if (result.rowCount === 0) {
      res.status(404).json({ message: "Capital no encontrada" });
      return;
    }

    res.json(result.rows[0]);
  } catch (error) {
    next(error);
  }
});

router.get("/landmarks", async (_req, res, next) => {
  try {
    const result = await query(
      "select landmarks.id, landmarks.name, landmarks.type, capitals.name as capital from landmarks join capitals on landmarks.capital_id = capitals.id order by landmarks.name"
    );
    res.json(result.rows);
  } catch (error) {
    next(error);
  }
});
