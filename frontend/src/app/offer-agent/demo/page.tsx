"use client";

import { useState, useCallback, useRef } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/hooks/use-toast";
import { Loader2, Play, Mail, ArrowRight, Sparkles, Check } from "lucide-react";
import Link from "next/link";

import { FileDropZone } from "@/components/demo/FileDropZone";
import { CustomerSelector } from "@/components/demo/CustomerSelector";
import { ToolVisualization } from "@/components/demo/ToolVisualization";
import {
  DEMO_CUSTOMERS,
  DEMO_OFFER,
  DEMO_TOOL_SEQUENCE,
  DEMO_ORDER_TEXT,
} from "@/lib/demo-data";

// Helper to get confidence badge color classes
function getConfidenceBadgeClasses(confidence: number): string {
  if (confidence >= 90) return "bg-green-500 hover:bg-green-500/90";
  if (confidence >= 75) return "bg-yellow-500 hover:bg-yellow-500/90 text-black";
  return "bg-red-500 hover:bg-red-500/90";
}

export default function DemoPage() {
  const { toast } = useToast();

  // Form state
  const [selectedCustomerId, setSelectedCustomerId] = useState(DEMO_CUSTOMERS[0].id);
  const [orderText, setOrderText] = useState(DEMO_ORDER_TEXT);
  const [files, setFiles] = useState<Array<{ name: string; type: string; size: number }>>([]);

  // Processing state
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentToolIndex, setCurrentToolIndex] = useState(0);
  const [showResult, setShowResult] = useState(false);
  const [emailSent, setEmailSent] = useState(false);
  const [isSendingEmail, setIsSendingEmail] = useState(false);

  // Ref to prevent double email sending
  const emailSentRef = useRef(false);

  const sendEmail = useCallback(async () => {
    if (emailSentRef.current) return;
    emailSentRef.current = true;
    setIsSendingEmail(true);

    try {
      const response = await fetch("/api/demo/send-email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          offer: DEMO_OFFER,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to send email");
      }

      setEmailSent(true);
      toast({
        title: "Email Sent",
        description: "Offer confirmation email has been sent automatically",
      });
    } catch (error) {
      toast({
        title: "Email Failed",
        description: "Could not send email. Check your email configuration.",
        variant: "destructive",
      });
    } finally {
      setIsSendingEmail(false);
    }
  }, [toast]);

  const runToolSequence = useCallback(async () => {
    setIsProcessing(true);
    setCurrentToolIndex(0);
    setShowResult(false);
    setEmailSent(false);
    emailSentRef.current = false;

    for (let i = 0; i < DEMO_TOOL_SEQUENCE.length; i++) {
      setCurrentToolIndex(i);
      await new Promise((resolve) => setTimeout(resolve, DEMO_TOOL_SEQUENCE[i].duration));
      setCurrentToolIndex(i + 1);
    }

    setIsProcessing(false);
    setShowResult(true);

    toast({
      title: "Offer Generated",
      description: `Offer ${DEMO_OFFER.offer_number} created with ${DEMO_OFFER.lines.length} products`,
    });

    // Auto-send email after offer is generated
    sendEmail();
  }, [toast, sendEmail]);

  const handleReset = () => {
    setCurrentToolIndex(0);
    setShowResult(false);
    setIsProcessing(false);
    setEmailSent(false);
    emailSentRef.current = false;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Sparkles className="h-8 w-8 text-primary" />
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Demo: AI Offer Generation</h1>
          <p className="text-muted-foreground">
            Experience the AI-powered offer automation workflow
          </p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Input Section */}
        <Card>
          <CardHeader>
            <CardTitle>Input</CardTitle>
            <CardDescription>
              Configure the demo offer request
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* File Drop Zone */}
            <div className="space-y-2">
              <Label>Attachments (Visual Only)</Label>
              <FileDropZone
                onFilesChanged={setFiles}
                className="w-full"
              />
            </div>

            {/* Customer Selector */}
            <div className="space-y-2">
              <Label>Customer</Label>
              <CustomerSelector
                value={selectedCustomerId}
                onValueChange={setSelectedCustomerId}
                disabled={isProcessing}
              />
            </div>

            {/* Order Text */}
            <div className="space-y-2">
              <Label>Order Request</Label>
              <Textarea
                value={orderText}
                onChange={(e) => setOrderText(e.target.value)}
                rows={10}
                disabled={isProcessing}
                className="font-mono text-sm"
              />
            </div>

            {/* Process Button */}
            <Button
              onClick={runToolSequence}
              disabled={isProcessing || showResult}
              className="w-full"
              size="lg"
            >
              {isProcessing ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : showResult ? (
                <>
                  Offer Generated
                </>
              ) : (
                <>
                  <Play className="mr-2 h-4 w-4" />
                  Process Offer
                </>
              )}
            </Button>

            {showResult && (
              <Button
                onClick={handleReset}
                variant="outline"
                className="w-full"
              >
                Reset Demo
              </Button>
            )}
          </CardContent>
        </Card>

        {/* Tool Visualization Section */}
        <Card>
          <CardHeader>
            <CardTitle>AI Workflow</CardTitle>
            <CardDescription>
              Watch the AI tools process your request
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ToolVisualization
              tools={DEMO_TOOL_SEQUENCE}
              currentToolIndex={currentToolIndex}
              isProcessing={isProcessing}
            />
          </CardContent>
        </Card>
      </div>

      {/* Result Section */}
      {showResult && (
        <Card className="border-green-500/50 bg-green-500/5">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  Generated Offer
                  <Badge variant="default" className="bg-green-500">
                    Ready
                  </Badge>
                </CardTitle>
                <CardDescription>
                  {DEMO_OFFER.offer_number}
                </CardDescription>
              </div>
              {/* Email status */}
              <div className="flex items-center gap-2 text-sm">
                {isSendingEmail ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                    <span className="text-muted-foreground">Sending email...</span>
                  </>
                ) : emailSent ? (
                  <>
                    <Check className="h-4 w-4 text-green-500" />
                    <span className="text-green-600">Email sent</span>
                  </>
                ) : (
                  <>
                    <Mail className="h-4 w-4 text-muted-foreground" />
                    <span className="text-muted-foreground">Email pending</span>
                  </>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-6 md:grid-cols-2">
              {/* Customer Info */}
              <div className="space-y-2">
                <h4 className="font-medium">Customer</h4>
                <div className="text-sm space-y-1">
                  <p className="font-medium">{DEMO_OFFER.customer.name}</p>
                  <p className="text-muted-foreground">{DEMO_OFFER.customer.street}</p>
                  <p className="text-muted-foreground">
                    {DEMO_OFFER.customer.postal_code} {DEMO_OFFER.customer.city}
                  </p>
                  <p className="text-muted-foreground">{DEMO_OFFER.customer.contact_person}</p>
                </div>
              </div>

              {/* Summary */}
              <div className="space-y-2">
                <h4 className="font-medium">Summary</h4>
                <div className="text-sm space-y-1">
                  <p>{DEMO_OFFER.lines.length} products matched</p>
                  <p className="text-2xl font-bold">
                    €{DEMO_OFFER.total_amount.toFixed(2)}
                  </p>
                  <p className="text-muted-foreground text-xs">
                    Created: {new Date(DEMO_OFFER.created_at).toLocaleString("fi-FI")}
                  </p>
                </div>
              </div>
            </div>

            {/* Product Lines Preview */}
            <div className="mt-6">
              <h4 className="font-medium mb-3">Matched Products</h4>
              <div className="space-y-2">
                {DEMO_OFFER.lines.map((line) => (
                  <div
                    key={line.id}
                    className="flex items-center justify-between p-3 bg-background rounded-lg border"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs text-muted-foreground">
                          {line.product_code}
                        </span>
                        <span className="font-medium">{line.product_name}</span>
                      </div>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        "{line.original_customer_term}" → {line.quantity} pcs
                      </p>
                    </div>
                    <div className="flex items-center gap-4">
                      <Badge className={getConfidenceBadgeClasses(line.ai_confidence)}>
                        {line.ai_confidence}%
                      </Badge>
                      <span className="font-medium">
                        €{line.total_price.toFixed(2)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div className="mt-6 flex justify-end">
              <Button asChild variant="default">
                <Link href={`/offer-agent/demo/${DEMO_OFFER.id}`}>
                  View Offer Details
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
