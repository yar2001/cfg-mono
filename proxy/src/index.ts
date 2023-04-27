import express from 'express';
import httpProxy from 'http-proxy';
import cors from 'cors';

const port = 9000;

const proxy = httpProxy.createProxyServer({});
const app = express();

app.use(cors());

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

app.listen(port, () => console.log(`SSR Server is now running on http://localhost:${port}`));
