import React from 'react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';

interface MonthSelectorProps {
  value: string | undefined; // 'YYYY-MM'
  onValueChange: (value: string) => void;
  availableMonths?: string[]; // optional, not required for datepicker
}

export function MonthSelector({ value, onValueChange }: MonthSelectorProps) {
  // Parse incoming value 'YYYY-MM' to Date
  const parse = (v?: string) => {
    if (!v) return new Date();
    const parts = v.split('-');
    if (parts.length !== 2) return new Date();
    const y = parseInt(parts[0], 10);
    const m = parseInt(parts[1], 10) - 1;
    return new Date(y, m, 1);
  };

  const selected = parse(value);

  const handleChange = (date: Date | null) => {
    if (!date) return;
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    onValueChange(`${y}-${m}`);
  };

  return (
    <DatePicker
      selected={selected}
      onChange={handleChange}
      dateFormat="MM/yyyy"
      showMonthYearPicker
      showFullMonthYearPicker={false}
      className="w-full"
    />
  );
}

export default MonthSelector;
