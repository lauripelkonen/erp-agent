"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { useToast } from "@/hooks/use-toast";
import { api } from "@/lib/api";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Loader2, Send, Trash2, RefreshCw, Eye, EyeOff, Settings2 } from "lucide-react";
import { useClientConfig } from "@/hooks/use-client-config";

interface OrderLine {
  id: string;
  product_code: string;
  product_name: string;
  description?: string;
  quantity: number;
  unit_price?: number;
  total_price?: number;
  ai_confidence: number;
  ai_reasoning?: string;
  original_customer_term: string;
  selected: boolean;
}

interface PendingOffer {
  id: string;
  offer_number: string;
  customer_name: string;
  customer_email: string;
  created_at: string;
  total_amount: number;
  lines: OrderLine[];
}

// Column configuration type
interface ColumnConfig {
  key: keyof OrderLine | "actions";
  label: string;
  visible: boolean;
  required?: boolean;
}

const defaultColumns: ColumnConfig[] = [
  { key: "selected", label: "", visible: true, required: true },
  { key: "product_code", label: "Product Code", visible: true },
  { key: "product_name", label: "Product Name", visible: true },
  { key: "description", label: "Description", visible: false },
  { key: "original_customer_term", label: "Original Request", visible: true },
  { key: "quantity", label: "Qty", visible: true },
  { key: "unit_price", label: "Unit Price", visible: true },
  { key: "total_price", label: "Total", visible: true },
  { key: "ai_confidence", label: "Match %", visible: true },
  { key: "ai_reasoning", label: "AI Reasoning", visible: false },
];

export default function ReviewOffersPage() {
  const { toast } = useToast();
  const { config, isLoading: configLoading } = useClientConfig();

  const [offers, setOffers] = useState<PendingOffer[]>([]);
  const [selectedOffer, setSelectedOffer] = useState<PendingOffer | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [offerToDelete, setOfferToDelete] = useState<PendingOffer | null>(null);
  const [columns, setColumns] = useState<ColumnConfig[]>(defaultColumns);
  const [showColumnSettings, setShowColumnSettings] = useState(false);

  // Apply client config to columns
  useEffect(() => {
    if (config?.columnConfig) {
      setColumns(config.columnConfig as ColumnConfig[]);
    }
  }, [config]);

  const fetchOffers = async () => {
    setIsLoading(true);
    try {
      const data = await api.getPendingOffers();
      // Initialize all lines as selected
      const offersWithSelection = (data.offers || []).map((offer: PendingOffer) => ({
        ...offer,
        lines: offer.lines.map((line: OrderLine) => ({ ...line, selected: true })),
      }));
      setOffers(offersWithSelection);

      if (offersWithSelection.length > 0 && !selectedOffer) {
        setSelectedOffer(offersWithSelection[0]);
      }
    } catch (error) {
      console.error("Failed to fetch offers:", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchOffers();
  }, []);

  const toggleLineSelection = (lineId: string) => {
    if (!selectedOffer) return;

    const updatedLines = selectedOffer.lines.map((line) =>
      line.id === lineId ? { ...line, selected: !line.selected } : line
    );

    const updatedOffer = { ...selectedOffer, lines: updatedLines };
    setSelectedOffer(updatedOffer);
    setOffers(offers.map((o) => (o.id === selectedOffer.id ? updatedOffer : o)));
  };

  const toggleAllLines = (checked: boolean) => {
    if (!selectedOffer) return;

    const updatedLines = selectedOffer.lines.map((line) => ({
      ...line,
      selected: checked,
    }));

    const updatedOffer = { ...selectedOffer, lines: updatedLines };
    setSelectedOffer(updatedOffer);
    setOffers(offers.map((o) => (o.id === selectedOffer.id ? updatedOffer : o)));
  };

  const handleSendToERP = async () => {
    if (!selectedOffer) return;

    const selectedLines = selectedOffer.lines.filter((line) => line.selected);
    if (selectedLines.length === 0) {
      toast({
        title: "No lines selected",
        description: "Please select at least one line to send to ERP",
        variant: "destructive",
      });
      return;
    }

    setIsSubmitting(true);
    try {
      await api.sendToERP(selectedOffer.id, selectedLines.map((line) => line.id));

      toast({
        title: "Offer Sent",
        description: `Offer ${selectedOffer.offer_number} has been sent to ERP`,
      });

      // Remove from list and select next
      const remainingOffers = offers.filter((o) => o.id !== selectedOffer.id);
      setOffers(remainingOffers);
      setSelectedOffer(remainingOffers[0] || null);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to send offer to ERP",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!offerToDelete) return;

    setIsSubmitting(true);
    try {
      await api.deleteOffer(offerToDelete.id);

      toast({
        title: "Offer Deleted",
        description: `Offer ${offerToDelete.offer_number} has been deleted`,
      });

      const remainingOffers = offers.filter((o) => o.id !== offerToDelete.id);
      setOffers(remainingOffers);
      if (selectedOffer?.id === offerToDelete.id) {
        setSelectedOffer(remainingOffers[0] || null);
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to delete offer",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
      setDeleteDialogOpen(false);
      setOfferToDelete(null);
    }
  };

  const toggleColumnVisibility = (key: string) => {
    setColumns(
      columns.map((col) =>
        col.key === key && !col.required ? { ...col, visible: !col.visible } : col
      )
    );
  };

  const visibleColumns = columns.filter((col) => col.visible);
  const allSelected = selectedOffer?.lines.every((line) => line.selected) ?? false;
  const someSelected = (selectedOffer?.lines.some((line) => line.selected) && !allSelected) ?? false;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Review Offers</h1>
          <p className="text-muted-foreground">
            Review and approve offers before sending to ERP
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowColumnSettings(!showColumnSettings)}
          >
            <Settings2 className="mr-2 h-4 w-4" />
            Columns
          </Button>
          <Button variant="outline" size="sm" onClick={fetchOffers}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
        </div>
      </div>

      {showColumnSettings && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">Column Visibility</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-4">
              {columns
                .filter((col) => col.key !== "selected" && col.key !== "actions")
                .map((col) => (
                  <label key={col.key} className="flex items-center gap-2">
                    <Checkbox
                      checked={col.visible}
                      onCheckedChange={() => toggleColumnVisibility(col.key)}
                      disabled={col.required}
                    />
                    <span className="text-sm">{col.label}</span>
                  </label>
                ))}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-6 lg:grid-cols-4">
        {/* Offer List */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-lg">Pending Offers</CardTitle>
            <CardDescription>{offers.length} awaiting review</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin" />
              </div>
            ) : offers.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">
                No pending offers
              </p>
            ) : (
              <div className="space-y-2">
                {offers.map((offer) => (
                  <button
                    key={offer.id}
                    onClick={() => setSelectedOffer(offer)}
                    className={`w-full text-left p-3 rounded-lg border transition-colors ${
                      selectedOffer?.id === offer.id
                        ? "border-primary bg-primary/5"
                        : "hover:bg-accent"
                    }`}
                  >
                    <div className="font-medium text-sm">{offer.customer_name}</div>
                    <div className="text-xs text-muted-foreground">
                      {offer.offer_number}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {offer.lines.length} lines
                    </div>
                  </button>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Offer Details */}
        <Card className="lg:col-span-3">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>
                  {selectedOffer?.offer_number || "Select an Offer"}
                </CardTitle>
                {selectedOffer && (
                  <CardDescription>
                    {selectedOffer.customer_name} - {selectedOffer.customer_email}
                  </CardDescription>
                )}
              </div>
              {selectedOffer && (
                <div className="flex gap-2">
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => {
                      setOfferToDelete(selectedOffer);
                      setDeleteDialogOpen(true);
                    }}
                    disabled={isSubmitting}
                  >
                    <Trash2 className="mr-2 h-4 w-4" />
                    Delete
                  </Button>
                  <Button
                    size="sm"
                    onClick={handleSendToERP}
                    disabled={isSubmitting}
                  >
                    {isSubmitting ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Send className="mr-2 h-4 w-4" />
                    )}
                    Send to ERP
                  </Button>
                </div>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {!selectedOffer ? (
              <p className="text-center text-muted-foreground py-8">
                Select an offer from the list to review
              </p>
            ) : (
              <div className="rounded-md border overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      {visibleColumns.map((col) => (
                        <TableHead key={col.key} className="whitespace-nowrap">
                          {col.key === "selected" ? (
                            <Checkbox
                              checked={allSelected}
                              ref={(el) => {
                                if (el) (el as unknown as HTMLInputElement).indeterminate = someSelected;
                              }}
                              onCheckedChange={(checked) =>
                                toggleAllLines(checked as boolean)
                              }
                            />
                          ) : (
                            col.label
                          )}
                        </TableHead>
                      ))}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {selectedOffer.lines.map((line) => (
                      <TableRow
                        key={line.id}
                        className={!line.selected ? "opacity-50" : ""}
                      >
                        {visibleColumns.map((col) => (
                          <TableCell key={col.key} className="whitespace-nowrap">
                            {col.key === "selected" ? (
                              <Checkbox
                                checked={line.selected}
                                onCheckedChange={() => toggleLineSelection(line.id)}
                              />
                            ) : col.key === "ai_confidence" ? (
                              <Badge
                                variant={
                                  line.ai_confidence >= 80
                                    ? "default"
                                    : line.ai_confidence >= 60
                                    ? "secondary"
                                    : "destructive"
                                }
                              >
                                {line.ai_confidence}%
                              </Badge>
                            ) : col.key === "unit_price" || col.key === "total_price" ? (
                              line[col.key] !== undefined
                                ? `€${(line[col.key] as number).toFixed(2)}`
                                : "-"
                            ) : (
                              (line[col.key as keyof OrderLine] as string | number) || "-"
                            )}
                          </TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}

            {selectedOffer && (
              <div className="mt-4 flex justify-between items-center">
                <div className="text-sm text-muted-foreground">
                  {selectedOffer.lines.filter((l) => l.selected).length} of{" "}
                  {selectedOffer.lines.length} lines selected
                </div>
                <div className="text-lg font-semibold">
                  Total: €
                  {selectedOffer.lines
                    .filter((l) => l.selected)
                    .reduce((sum, l) => sum + (l.total_price || 0), 0)
                    .toFixed(2)}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Offer?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete offer {offerToDelete?.offer_number}?
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete}>Delete</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
