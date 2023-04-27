import express from 'express';
import httpProxy from 'http-proxy';
import cors from 'cors';
import axios from 'axios';

const port = 9000;

const proxy = httpProxy.createProxyServer({});
const app = express();

app.use(cors());
app.use(express.json({ limit: '50mb' }));

app.use('/batch/:lang', async (req, res) => {
  const input = req.body as { codes: { text: string; name: string }[] };
  const output = [] as { CSN: string }[];
  for (const code of input.codes) {
    const { data } = await axios.post(`http://${req.params.lang}:5000/getCFG`, { code: code.text });
    output.push({ CSN: data.CSN });
  }
  res.json(output);
});

app.use('/:lang', (req, res) => {
  proxy.web(
    req,
    res,
    {
      target: `http://${req.params.lang}:5000`,
      changeOrigin: true,
    },
    (err) => {
      console.error(err);
      res.status(500).send(err.message);
    }
  );
});

app.listen(port, () => console.log(`Server is now running on http://localhost:${port}`));
