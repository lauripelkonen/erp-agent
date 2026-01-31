"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { useToast } from "@/hooks/use-toast";
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
  Loader2,
  Send,
  Trash2,
  Mail,
  ArrowLeft,
  Plus,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import {
  DEMO_OFFER,
  DEMO_CUSTOMERS,
  DEMO_PRODUCTS,
  FALLBACK_PRODUCTS,
  type DemoOfferLine,
  type DemoCustomer,
} from "@/lib/demo-data";

// Helper to get confidence badge color classes
function getConfidenceBadgeClasses(confidence: number): string {
  if (confidence >= 90) return "bg-green-500 hover:bg-green-500/90";
  if (confidence >= 75) return "bg-yellow-500 hover:bg-yellow-500/90 text-black";
  return "bg-red-500 hover:bg-red-500/90";
}

// Counter for fallback products
let fallbackCounter = 0;

// Lookup product by code or return fallback
function lookupProduct(code: string): { name: string; unit_price: number } {
  const upperCode = code.toUpperCase();
  if (DEMO_PRODUCTS[upperCode]) {
    return DEMO_PRODUCTS[upperCode];
  }
  // Return a cycling fallback product
  const fallback = FALLBACK_PRODUCTS[fallbackCounter % FALLBACK_PRODUCTS.length];
  fallbackCounter++;
  return { name: fallback.name, unit_price: fallback.unit_price };
}

export default function OfferInspectionPage() {
  const { toast } = useToast();
  const router = useRouter();

  // Local state for editable offer (visual only, not persisted)
  const [customer, setCustomer] = useState<DemoCustomer>(DEMO_OFFER.customer);
  const [lines, setLines] = useState<DemoOfferLine[]>(DEMO_OFFER.lines);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [isSendingToErp, setIsSendingToErp] = useState(false);
  const [isSendingEmail, setIsSendingEmail] = useState(false);

  // Track which product code is being edited
  const [editingLineId, setEditingLineId] = useState<string | null>(null);
  const [editingCode, setEditingCode] = useState("");

  // Calculate total
  const totalAmount = lines.reduce((sum, line) => sum + line.total_price, 0);

  const handleCustomerChange = (customerId: string) => {
    const newCustomer = DEMO_CUSTOMERS.find((c) => c.id === customerId);
    if (newCustomer) {
      setCustomer(newCustomer);
      toast({
        title: "Customer Updated",
        description: `Changed to ${newCustomer.name}`,
      });
    }
  };

  const handleQuantityChange = (lineId: string, newQuantity: number) => {
    setLines(
      lines.map((line) =>
        line.id === lineId
          ? {
              ...line,
              quantity: newQuantity,
              total_price: newQuantity * line.unit_price,
            }
          : line
      )
    );
  };

  const handleStartEditCode = (line: DemoOfferLine) => {
    setEditingLineId(line.id);
    setEditingCode(line.product_code);
  };

  const handleCodeChange = (value: string) => {
    setEditingCode(value.toUpperCase());
  };

  const handleCodeBlur = () => {
    if (editingLineId && editingCode) {
      applyCodeChange(editingLineId, editingCode);
    }
    setEditingLineId(null);
    setEditingCode("");
  };

  const handleCodeKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      if (editingLineId && editingCode) {
        applyCodeChange(editingLineId, editingCode);
      }
      setEditingLineId(null);
      setEditingCode("");
    } else if (e.key === "Escape") {
      setEditingLineId(null);
      setEditingCode("");
    }
  };

  const applyCodeChange = (lineId: string, newCode: string) => {
    const product = lookupProduct(newCode);
    setLines(
      lines.map((line) =>
        line.id === lineId
          ? {
              ...line,
              product_code: newCode.toUpperCase(),
              product_name: product.name,
              unit_price: product.unit_price,
              total_price: line.quantity * product.unit_price,
              ai_confidence: 100, // Manual selection = 100% confidence
              ai_reasoning: "Manually selected by user",
            }
          : line
      )
    );
    toast({
      title: "Product Updated",
      description: `Changed to ${product.name}`,
    });
  };

  const handleRemoveLine = (lineId: string) => {
    setLines(lines.filter((line) => line.id !== lineId));
    toast({
      title: "Line Removed",
      description: "Product line has been removed from the offer",
    });
  };

  const handleAddLine = () => {
    const newLine: DemoOfferLine = {
      id: `line-${Date.now()}`,
      product_code: "NEW-PRODUCT",
      product_name: "New Product",
      original_customer_term: "manual entry",
      quantity: 1,
      unit_price: 0,
      total_price: 0,
      ai_confidence: 100,
      ai_reasoning: "Manually added by user",
    };
    setLines([...lines, newLine]);
    toast({
      title: "Line Added",
      description: "New product line added to the offer",
    });
  };

  const handleSendToErp = async () => {
    setIsSendingToErp(true);
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setIsSendingToErp(false);

    toast({
      title: "Sent to ERP",
      description: `Offer ${DEMO_OFFER.offer_number} has been sent to ERP successfully`,
    });
  };

  const handleResendEmail = async () => {
    setIsSendingEmail(true);

    try {
      const response = await fetch("/api/demo/send-email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          offer: {
            ...DEMO_OFFER,
            customer,
            lines,
            total_amount: totalAmount,
          },
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to send email");
      }

      toast({
        title: "Email Sent",
        description: "Offer confirmation email has been resent",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to send email. Check your email configuration.",
        variant: "destructive",
      });
    } finally {
      setIsSendingEmail(false);
    }
  };

  const handleDelete = () => {
    setShowDeleteDialog(false);
    toast({
      title: "Offer Deleted",
      description: `Offer ${DEMO_OFFER.offer_number} has been deleted`,
    });
    router.push("/offer-agent/demo");
  };

  return (
    <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button asChild variant="ghost" size="icon">
            <Link href="/offer-agent/demo">
              <ArrowLeft className="h-4 w-4" />
            </Link>
          </Button>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">
              Offer: {DEMO_OFFER.offer_number}
            </h1>
            <p className="text-muted-foreground">
              Review and edit offer details (demo - changes are not persisted)
            </p>
          </div>
        </div>

        {/* Customer Card */}
        <Card>
          <CardHeader>
            <CardTitle>Customer</CardTitle>
            <CardDescription>
              Select the customer for this offer
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Select
                  value={customer.id}
                  onValueChange={handleCustomerChange}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {DEMO_CUSTOMERS.map((c) => (
                      <SelectItem key={c.id} value={c.id}>
                        {c.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="text-sm space-y-1">
                <p className="font-medium">{customer.name}</p>
                <p className="text-muted-foreground">{customer.street}</p>
                <p className="text-muted-foreground">
                  {customer.postal_code} {customer.city}
                </p>
                <p className="text-muted-foreground">{customer.contact_person}</p>
                <p className="text-primary">{customer.payment_terms}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Product Lines Card */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Product Lines</CardTitle>
                <CardDescription>
                  Review and edit matched products. Click on a product code to change it.
                </CardDescription>
              </div>
              <Button onClick={handleAddLine} variant="outline" size="sm">
                <Plus className="mr-2 h-4 w-4" />
                Add Line
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="whitespace-nowrap w-32">Code</TableHead>
                    <TableHead className="whitespace-nowrap">Product</TableHead>
                    <TableHead className="whitespace-nowrap w-24">Qty</TableHead>
                    <TableHead className="whitespace-nowrap text-right w-24">Unit Price</TableHead>
                    <TableHead className="whitespace-nowrap text-right w-24">Total</TableHead>
                    <TableHead className="whitespace-nowrap text-center w-20">AI %</TableHead>
                    <TableHead className="whitespace-nowrap min-w-[200px]">AI Reasoning</TableHead>
                    <TableHead className="whitespace-nowrap w-16"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {lines.map((line) => (
                    <TableRow key={line.id}>
                      <TableCell>
                        {editingLineId === line.id ? (
                          <Input
                            value={editingCode}
                            onChange={(e) => handleCodeChange(e.target.value)}
                            onBlur={handleCodeBlur}
                            onKeyDown={handleCodeKeyDown}
                            className="font-mono text-xs w-28"
                            autoFocus
                          />
                        ) : (
                          <button
                            onClick={() => handleStartEditCode(line)}
                            className="font-mono text-xs text-left hover:bg-muted px-2 py-1 rounded cursor-text w-full"
                            title="Click to edit product code"
                          >
                            {line.product_code}
                          </button>
                        )}
                      </TableCell>
                      <TableCell className="font-medium">
                        {line.product_name}
                      </TableCell>
                      <TableCell>
                        <Input
                          type="number"
                          min={1}
                          value={line.quantity}
                          onChange={(e) =>
                            handleQuantityChange(
                              line.id,
                              parseInt(e.target.value) || 1
                            )
                          }
                          className="w-20"
                        />
                      </TableCell>
                      <TableCell className="text-right">
                        €{line.unit_price.toFixed(2)}
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        €{line.total_price.toFixed(2)}
                      </TableCell>
                      <TableCell className="text-center">
                        <Badge className={getConfidenceBadgeClasses(line.ai_confidence)}>
                          {line.ai_confidence}%
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <span className="text-xs text-muted-foreground">
                          {line.ai_reasoning}
                        </span>
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleRemoveLine(line.id)}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            {/* Total */}
            <div className="mt-4 flex justify-end">
              <div className="text-right">
                <p className="text-sm text-muted-foreground">Total</p>
                <p className="text-2xl font-bold">€{totalAmount.toFixed(2)}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-3">
          <Button
            variant="destructive"
            onClick={() => setShowDeleteDialog(true)}
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Delete Offer
          </Button>

          <div className="flex-1" />

          <Button
            variant="outline"
            onClick={handleResendEmail}
            disabled={isSendingEmail}
          >
            {isSendingEmail ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Sending...
              </>
            ) : (
              <>
                <Mail className="mr-2 h-4 w-4" />
                Resend Email
              </>
            )}
          </Button>

          <Button
            onClick={handleSendToErp}
            disabled={isSendingToErp || lines.length === 0}
          >
            {isSendingToErp ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Sending...
              </>
            ) : (
              <>
                <Send className="mr-2 h-4 w-4" />
                Send to ERP
              </>
            )}
          </Button>
        </div>

        {/* Delete Confirmation Dialog */}
        <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete Offer?</AlertDialogTitle>
              <AlertDialogDescription>
                Are you sure you want to delete offer {DEMO_OFFER.offer_number}?
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
