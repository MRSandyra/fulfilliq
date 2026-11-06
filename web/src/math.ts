export const pct = (value:number|null|undefined) => value == null ? "N/A" : new Intl.NumberFormat("en-US", {style:"percent", maximumFractionDigits:1}).format(value);
export const brl = (value:number|null|undefined) => new Intl.NumberFormat("en-US", {style:"currency", currency:"BRL", maximumFractionDigits:0}).format(value ?? 0);
export const triage = (count:number, meanRisk:number, effectiveness:number, cost:number, penalty:number) => ({ avoided: count * meanRisk * effectiveness, net: count * (meanRisk * effectiveness * penalty - cost) });
