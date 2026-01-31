"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/hooks/use-toast";
import { Loader2, Send, Plus, Trash2 } from "lucide-react";
import { api } from "@/lib/api";

interface ProductLine {
  id: string;
  description: string;
  quantity: string;
}

interface OfferFormData {
  customerEmail: string;
  customerName: string;
  subject: string;
  body: string;
}

export default function CreateOfferPage() {
  const { toast } = useToast();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [productLines, setProductLines] = useState<ProductLine[]>([
    { id: "1", description: "", quantity: "1" },
  ]);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<OfferFormData>();

  const addProductLine = () => {
    setProductLines([
      ...productLines,
      { id: Date.now().toString(), description: "", quantity: "1" },
    ]);
  };

  const removeProductLine = (id: string) => {
    if (productLines.length > 1) {
      setProductLines(productLines.filter((line) => line.id !== id));
    }
  };

  const updateProductLine = (
    id: string,
    field: keyof ProductLine,
    value: string
  ) => {
    setProductLines(
      productLines.map((line) =>
        line.id === id ? { ...line, [field]: value } : line
      )
    );
  };

  const onSubmit = async (data: OfferFormData) => {
    setIsSubmitting(true);

    // Build the email body with product lines
    const productListText = productLines
      .filter((line) => line.description.trim())
      .map((line) => `${line.quantity}x ${line.description}`)
      .join("\n");

    const fullBody = `${data.body}\n\nTuotteet:\n${productListText}\n\nYt,\n${data.customerName}`;

    const emailData = {
      sender: data.customerEmail,
      subject: data.subject,
      body: fullBody,
      date: new Date().toISOString(),
      attachments: [],
    };

    try {
      const result = await api.createOffer(emailData);

      toast({
        title: "Offer Submitted",
        description: `Offer request submitted successfully. ${result.offer_number ? `Offer: ${result.offer_number}` : ""}`,
      });

      // Reset form
      reset();
      setProductLines([{ id: "1", description: "", quantity: "1" }]);
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to submit offer",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Create Offer</h1>
        <p className="text-muted-foreground">
          Manually create a new offer request
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Offer Request Details</CardTitle>
          <CardDescription>
            Fill in the customer and product information to create a new offer
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="customerEmail">Customer Email</Label>
                <Input
                  id="customerEmail"
                  type="email"
                  placeholder="customer@company.com"
                  {...register("customerEmail", {
                    required: "Email is required",
                    pattern: {
                      value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                      message: "Invalid email address",
                    },
                  })}
                />
                {errors.customerEmail && (
                  <p className="text-sm text-destructive">
                    {errors.customerEmail.message}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="customerName">Customer Name / Company</Label>
                <Input
                  id="customerName"
                  placeholder="Customer or Company Name"
                  {...register("customerName", {
                    required: "Customer name is required",
                  })}
                />
                {errors.customerName && (
                  <p className="text-sm text-destructive">
                    {errors.customerName.message}
                  </p>
                )}
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="subject">Subject</Label>
              <Input
                id="subject"
                placeholder="Tilaus / Tarjouspyyntö"
                {...register("subject", { required: "Subject is required" })}
              />
              {errors.subject && (
                <p className="text-sm text-destructive">
                  {errors.subject.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="body">Additional Notes</Label>
              <Textarea
                id="body"
                placeholder="Any additional information about the order..."
                rows={3}
                {...register("body")}
              />
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label>Products</Label>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={addProductLine}
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Add Product
                </Button>
              </div>

              <div className="space-y-3">
                {productLines.map((line, index) => (
                  <div key={line.id} className="flex gap-3">
                    <div className="w-20">
                      <Input
                        type="number"
                        min="1"
                        placeholder="Qty"
                        value={line.quantity}
                        onChange={(e) =>
                          updateProductLine(line.id, "quantity", e.target.value)
                        }
                      />
                    </div>
                    <div className="flex-1">
                      <Input
                        placeholder={`Product ${index + 1} description (e.g., DN50 Kaulus HST)`}
                        value={line.description}
                        onChange={(e) =>
                          updateProductLine(
                            line.id,
                            "description",
                            e.target.value
                          )
                        }
                      />
                    </div>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      onClick={() => removeProductLine(line.id)}
                      disabled={productLines.length === 1}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-end gap-3">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  reset();
                  setProductLines([{ id: "1", description: "", quantity: "1" }]);
                }}
              >
                Clear
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  <>
                    <Send className="mr-2 h-4 w-4" />
                    Submit Offer Request
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
