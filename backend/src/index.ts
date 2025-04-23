import Koa from 'koa';
import cors from '@koa/cors';
import Router from '@koa/router';
import axios from 'axios';

const app = new Koa();
const router = new Router();

// Enable CORS
app.use(cors());

// Health check endpoint
router.get('/health', (ctx: Koa.Context) => {
  ctx.body = { status: 'ok' };
});

// Travel warnings endpoint
router.get('/travel-warnings', async (ctx: Koa.Context) => {
  try {
    const { language = 'en' } = ctx.query;
    const response = await axios.get('https://www.auswaertiges-amt.de/opendata/travelwarning', {
      params: { language }
    });
    ctx.body = response.data;
  } catch (error) {
    ctx.status = 500;
    ctx.body = { error: 'Failed to fetch travel warnings' };
  }
});

// Travel warning detail endpoint
router.get('/travel-warnings/:id', async (ctx: Koa.Context) => {
  try {
    const { id } = ctx.params;
    const { language = 'en' } = ctx.query;
    const response = await axios.get(`https://www.auswaertiges-amt.de/opendata/travelwarning/${id}`, {
      params: { language }
    });
    ctx.body = response.data;
  } catch (error) {
    ctx.status = 500;
    ctx.body = { error: 'Failed to fetch travel warning details' };
  }
});

// Use routes
app.use(router.routes());
app.use(router.allowedMethods());

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
}); 