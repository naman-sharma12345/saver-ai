import { Link } from 'react-router-dom';

export const Privacy = () => (
  <div className="max-w-2xl mx-auto px-6 py-16">
    <p className="eyebrow">Plain-language summary</p>
    <h1 className="display-title mt-1">Terms and Privacy</h1>
    <p className="mt-4 text-ink-2 text-[17px]">This is a short, honest summary of how SaverAI treats your data. A full legal version will replace it before public launch.</p>
    <div className="mt-8 space-y-6 text-[16px] text-ink-2 leading-relaxed">
      <section><h2 className="text-ink font-semibold text-[19px]">What we store</h2><p>Your name, email, date of birth, the expenses, budgets and goals you enter, and (for under-18s) your parent or guardian's email. Nothing else.</p></section>
      <section><h2 className="text-ink font-semibold text-[19px]">How the AI works</h2><p>Categorising, forecasting and spotting unusual spending run on small models inside SaverAI. Your data is not sent to outside AI services.</p></section>
      <section><h2 className="text-ink font-semibold text-[19px]">Under 18</h2><p>A parent or guardian approves your account before we handle your data. We show no ads and do no tracking for marketing.</p></section>
      <section><h2 className="text-ink font-semibold text-[19px]">Your rights</h2><p>Download everything we hold, or delete your account and all its data, any time from Profile.</p></section>
    </div>
    <p className="mt-10"><Link to="/" className="text-accent font-medium">Back home</Link></p>
  </div>
);
