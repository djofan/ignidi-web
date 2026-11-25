import test from 'node:test';
import assert from 'node:assert/strict';
import { automationCases } from '../lib/automation-cases.ts';
import { runAutomation } from '../lib/automation-engine.ts';
const item = id => automationCases.find(value => value.id === id);
const run = (id, overrides = {}, context = []) => runAutomation(item(id), { ...item(id).presets[0].values, ...overrides }, context);

test('ten cases have researched repo and documentation sources; every preset executes', () => {
  assert.equal(automationCases.length, 10);
  assert.equal(new Set(automationCases.map(c => c.id)).size, 10);
  for (const c of automationCases) {
    assert.match(c.source.repo, /^https:\/\/github.com\//);
    assert.match(c.source.docs, /^https:\//);
    for (const preset of c.presets) {
      const result = runAutomation(c, preset.values);
      assert.equal(result.logs.length, 4);
      assert.equal(typeof result.summary, 'string');
    }
  }
});
test('lead email normalization prevents case and whitespace duplicates', () => {
  assert.equal(run('lead', { email: ' RANI@example.com ', existing: 'rani@example.com' }).output.newRecords, 0);
  assert.equal(run('lead').output.newRecords, 1);
  assert.equal(run('lead', { email: 'broken' }).status, 'error');
});
test('invoice calculates balance; paid and not-due invoices do not create reminders', () => {
  assert.equal(run('invoice').output.balance, 500000);
  assert.equal(run('invoice').status, 'waiting');
  assert.equal(run('invoice', { paid: '750000' }).output.draft, null);
  assert.equal(run('invoice', { days: '2' }).output.action, 'skip_not_due');
  assert.match(run('invoice', { days: '-3' }).output.draft, /3 hari/);
  assert.equal(run('invoice', { paid: '750001' }).status, 'error');
});
test('stock recommendation uses editable target and respects exact minimum', () => {
  assert.equal(run('stock').output.restock, 16);
  assert.equal(run('stock', { target: '35' }).output.restock, 31);
  assert.equal(run('stock', { stock: '10' }).output.restock, 0);
  assert.equal(run('stock', { target: '9' }).status, 'error');
});
test('report excludes cancellations and pending payments; rejects partial corrupt input', () => {
  assert.equal(run('report').output.sales, 205000);
  assert.equal(run('report', { rows: '' }).output.sales, 0);
  assert.equal(run('report', { rows: '20|selesai\n30|selesai' }).output.sales, 50);
  assert.equal(run('report', { rows: '20|selesai\nabc|selesai' }).status, 'error');
  assert.equal(run('report', { rows: '20|unknown' }).status, 'error');
  assert.equal(run('report', { rows: Array(51).fill('20|selesai').join('\n') }).status, 'error');
});
test('learning validates progress, completion, and consent', () => {
  assert.equal(run('learning').output.remaining, 2);
  assert.equal(run('learning').output.progress, 60);
  assert.equal(run('learning', { completed: '5' }).output.action, 'skip_completed');
  assert.equal(run('learning', { consent: 'no' }).output.action, 'skip_no_consent');
  assert.equal(run('learning', { completed: '6' }).status, 'error');
  assert.equal(run('learning', { total: '0', completed: '0' }).status, 'error');
});
test('support routes categories and urgency independently', () => {
  assert.equal(run('ticket').output.assignedTeam, 'Keuangan');
  assert.equal(run('ticket').output.responseHours, 2);
  assert.equal(run('ticket', { category: 'access', priority: 'normal' }).output.assignedTeam, 'Dukungan Teknis');
  assert.equal(run('ticket', { priority: 'normal' }).output.responseHours, 24);
  assert.equal(run('ticket', { category: 'tampered' }).status, 'error');
});
test('approval pauses, approves, and rejects without any payment execution', () => {
  assert.equal(run('expense').status, 'waiting');
  assert.equal(run('expense', { decision: 'approved' }).output.approvedBy, 'manager_demo');
  assert.equal(run('expense', { decision: 'rejected' }).output.action, 'rejected');
  assert.equal(run('expense', { amount: '1000000' }).output.approvedBy, 'admin_policy_demo');
  assert.equal(run('expense', { decision: 'approved' }).output.paymentSent, false);
});
test('order is idempotent within its explicit session memory and unpaid events are not recorded', () => {
  const first = run('order');
  assert.equal(first.output.rememberEvent, 'evt-demo-001');
  const second = run('order', {}, [first.output.rememberEvent]);
  assert.equal(second.output.action, 'skip_duplicate');
  assert.equal(second.output.rememberEvent, undefined);
  assert.equal(run('order', { payment: 'pending' }).output.rememberEvent, undefined);
});
test('contact cleaning accounts for every row and normalizes email casing', () => {
  const output = run('contacts').output;
  assert.deepEqual(output.contacts, ['rani@example.com', 'budi@example.com']);
  assert.equal(output.duplicates, 1);
  assert.equal(output.invalid.length, 1);
  assert.equal(output.inputCount, output.contacts.length + output.duplicates + output.invalid.length);
  assert.equal(run('contacts', { emails: '' }).output.inputCount, 0);
});
test('monitor retries transient failures with bounded backoff; authorization errors stop immediately', () => {
  const result = run('monitor');
  assert.equal(result.status, 'success');
  assert.equal(result.output.attempts.length, 3);
  assert.equal(result.output.totalDelay, 6);
  assert.equal(run('monitor', { responses: '503', retries: '2' }).output.attempts.length, 3);
  assert.equal(run('monitor', { responses: '503', retries: '0' }).status, 'error');
  assert.equal(run('monitor', { responses: '403,200' }).output.attempts.length, 1);
  assert.equal(run('monitor', { responses: '429,200' }).status, 'success');
  assert.equal(run('monitor', { responses: '200' }).output.totalDelay, 0);
  assert.equal(run('monitor', { responses: '999' }).status, 'error');
});
test('invalid numeric inputs fail instead of producing misleading output', () => {
  for (const value of ['', '-1', '1.5', 'NaN', 'Infinity', '999999999999999999']) assert.equal(run('stock', { stock: value }).status, 'error');
  assert.equal(run('lead', { name: 'a'.repeat(3001) }).status, 'error');
});
