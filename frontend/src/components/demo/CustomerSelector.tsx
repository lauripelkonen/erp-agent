"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { DEMO_CUSTOMERS, type DemoCustomer } from "@/lib/demo-data";

interface CustomerSelectorProps {
  value: string;
  onValueChange: (customerId: string) => void;
  disabled?: boolean;
}

export function CustomerSelector({ value, onValueChange, disabled }: CustomerSelectorProps) {
  const selectedCustomer = DEMO_CUSTOMERS.find((c) => c.id === value);

  return (
    <div className="space-y-2">
      <Select value={value} onValueChange={onValueChange} disabled={disabled}>
        <SelectTrigger>
          <SelectValue placeholder="Select customer" />
        </SelectTrigger>
        <SelectContent>
          {DEMO_CUSTOMERS.map((customer) => (
            <SelectItem key={customer.id} value={customer.id}>
              <div className="flex flex-col">
                <span>{customer.name}</span>
                <span className="text-xs text-muted-foreground">
                  #{customer.customer_number} - {customer.city}
                </span>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {selectedCustomer && (
        <div className="text-xs text-muted-foreground space-y-0.5 pl-1">
          <p>{selectedCustomer.street}</p>
          <p>{selectedCustomer.postal_code} {selectedCustomer.city}</p>
          <p>{selectedCustomer.contact_person}</p>
          <p className="text-primary">{selectedCustomer.payment_terms}</p>
        </div>
      )}
    </div>
  );
}
