import "dotenv/config";
import express from "express";
import { router } from "./routes.js";

const app = express();
const port = process.env.PORT || 3000;

app.use(express.json());
app.use("/api", router);

app.use((err, _req, res, _next) => {
  console.error(err);
  res.status(500).json({ message: "Error interno" });
});

app.listen(port, () => {
  console.log(`Servidor escuchando en http://localhost:${port}`);
});
