import facts from '../facts.json' with { type: 'json' };

const MONTH = /^20\d{2}-(0[1-9]|1[0-2])$/;
const VALID_DIMENSIONS = new Set(['crew', 'service', 'city', 'month']);

export function runTool(name, args) {
  if (name === 'estimate_conversion') {
    return { period: 'all demo estimates', rows: facts.estimates };
  }
  const start = args?.start_month;
  const end = args?.end_month; // exclusive, e.g. 2026-09 for August
  if (!MONTH.test(start || '') || !MONTH.test(end || '') ||
      start < '2025-01' || start >= end || end > '2026-09') {
    return { error: 'Use a valid month range within 2025-01 through 2026-08.' };
  }
  if (name === 'low_margin_jobs') {
    return { period: `${start} through month before ${end}`,
      rows: facts.low_margin_jobs.filter(x => x.month >= start && x.month < end)
        .sort((a, b) => a.gross_margin_pct - b.gross_margin_pct).slice(0, 10) };
  }
  if (name !== 'analyze_jobs' || !VALID_DIMENSIONS.has(args?.group_by)) {
    return { error: 'Unknown tool or grouping.' };
  }
  const grouped = new Map();
  for (const row of facts.aggregates) {
    if (row.dimension !== args.group_by || row.month < start || row.month >= end) continue;
    const value = grouped.get(row.name) || {
      group: row.name, jobs: 0, revenue: 0, gross_profit: 0,
      labor_cost: 0, material_cost: 0, labor_hours: 0, rework: 0,
    };
    for (const key of ['jobs', 'revenue', 'gross_profit', 'labor_cost',
                       'material_cost', 'labor_hours', 'rework']) value[key] += row[key];
    grouped.set(row.name, value);
  }
  return { period: `${start} through month before ${end}`, rows: [...grouped.values()]
    .sort((a, b) => a.group.localeCompare(b.group)).slice(0, 30).map(x => ({
      group: x.group, jobs: x.jobs, revenue: round(x.revenue),
      gross_profit: round(x.gross_profit),
      gross_margin_pct: x.revenue ? round(100 * x.gross_profit / x.revenue) : null,
      labor_cost: round(x.labor_cost), material_cost: round(x.material_cost),
      labor_hours: round(x.labor_hours), rework_rate_pct: x.jobs ? round(100 * x.rework / x.jobs) : null,
    })) };
}

const round = value => Math.round(value * 100) / 100;
