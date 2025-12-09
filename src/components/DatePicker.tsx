import { useState } from 'react';
import { format } from 'date-fns';
import { Calendar as CalendarIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { cn } from '@/lib/utils';

interface DatePickerProps {
  date: Date | undefined;
  onDateChange: (date: Date | undefined) => void;
  availableDates?: string[];
}

export function DatePicker({ date, onDateChange, availableDates = [] }: DatePickerProps) {
  const [open, setOpen] = useState(false);

  const availableDateSet = new Set(availableDates);

  const isDateAvailable = (day: Date) => {
    const dateStr = format(day, 'yyyy-MM-dd');
    return availableDateSet.has(dateStr);
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          className={cn(
            'w-full justify-start text-left font-normal',
            !date && 'text-muted-foreground'
          )}
        >
          <CalendarIcon className="mr-2 h-4 w-4" />
          {date ? format(date, 'PPP') : <span>Pick a date</span>}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0 bg-popover" align="start">
        <Calendar
          mode="single"
          selected={date}
          onSelect={(newDate) => {
            onDateChange(newDate);
            setOpen(false);
          }}
          modifiers={{
            available: (day) => isDateAvailable(day),
          }}
          modifiersStyles={{
            available: {
              fontWeight: 'bold',
              backgroundColor: 'hsl(var(--primary) / 0.1)',
            },
          }}
          disabled={(day) => day > new Date()}
          initialFocus
          className="pointer-events-auto"
        />
      </PopoverContent>
    </Popover>
  );
}
