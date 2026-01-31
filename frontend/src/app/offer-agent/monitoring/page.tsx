"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { RefreshCw, Clock, CheckCircle, XCircle, Loader2, AlertCircle } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

interface ProcessingOffer {
  id: string;
  customer_name: string;
  subject: string;
  status: "processing" | "completed" | "failed" | "pending_review";
  progress: number;
  current_step: string;
  created_at: string;
  updated_at: string;
  errors?: string[];
}

const statusConfig = {
  processing: {
    label: "Processing",
    color: "bg-blue-500",
    icon: Loader2,
    variant: "default" as const,
  },
  completed: {
    label: "Completed",
    color: "bg-green-500",
    icon: CheckCircle,
    variant: "default" as const,
  },
  failed: {
    label: "Failed",
    color: "bg-red-500",
    icon: XCircle,
    variant: "destructive" as const,
  },
  pending_review: {
    label: "Pending Review",
    color: "bg-yellow-500",
    icon: Clock,
    variant: "secondary" as const,
  },
};

export default function MonitoringPage() {
  const [offers, setOffers] = useState<ProcessingOffer[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchOffers = async () => {
    try {
      const response = await fetch("/api/offers/status");

      if (response.ok) {
        const data = await response.json();
        setOffers(data.offers || []);
      }
    } catch (error) {
      console.error("Failed to fetch offers:", error);
    } finally {
      setIsLoading(false);
      setLastUpdated(new Date());
    }
  };

  useEffect(() => {
    fetchOffers();

    // Poll every 10 seconds
    const interval = setInterval(fetchOffers, 10000);
    return () => clearInterval(interval);
  }, []);

  const processingOffers = offers.filter((o) => o.status === "processing");
  const pendingOffers = offers.filter((o) => o.status === "pending_review");
  const completedOffers = offers.filter((o) => o.status === "completed");
  const failedOffers = offers.filter((o) => o.status === "failed");

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Offer Monitoring</h1>
          <p className="text-muted-foreground">
            Real-time status of offers being processed
          </p>
        </div>
        <div className="flex items-center gap-4">
          {lastUpdated && (
            <span className="text-sm text-muted-foreground">
              Last updated: {formatDistanceToNow(lastUpdated, { addSuffix: true })}
            </span>
          )}
          <Button variant="outline" size="sm" onClick={fetchOffers}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center">
              <Loader2 className="mr-2 h-4 w-4 text-blue-500" />
              Processing
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{processingOffers.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center">
              <Clock className="mr-2 h-4 w-4 text-yellow-500" />
              Pending Review
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{pendingOffers.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center">
              <CheckCircle className="mr-2 h-4 w-4 text-green-500" />
              Completed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{completedOffers.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center">
              <XCircle className="mr-2 h-4 w-4 text-red-500" />
              Failed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{failedOffers.length}</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Active Processing</CardTitle>
          <CardDescription>
            Offers currently being processed by the agent
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : offers.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <AlertCircle className="h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-muted-foreground">No offers in processing queue</p>
              <p className="text-sm text-muted-foreground">
                Offers will appear here when they start processing
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {offers.map((offer) => {
                const config = statusConfig[offer.status];
                const StatusIcon = config.icon;

                return (
                  <div
                    key={offer.id}
                    className="flex items-center gap-4 rounded-lg border p-4"
                  >
                    <div className={`h-2 w-2 rounded-full ${config.color}`} />

                    <div className="flex-1 space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{offer.customer_name}</span>
                        <Badge variant={config.variant}>
                          <StatusIcon className={`mr-1 h-3 w-3 ${offer.status === "processing" ? "animate-spin" : ""}`} />
                          {config.label}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">{offer.subject}</p>
                      {offer.status === "processing" && (
                        <div className="space-y-1">
                          <div className="flex items-center justify-between text-xs">
                            <span>{offer.current_step}</span>
                            <span>{offer.progress}%</span>
                          </div>
                          <Progress value={offer.progress} className="h-1" />
                        </div>
                      )}
                      {offer.errors && offer.errors.length > 0 && (
                        <p className="text-sm text-destructive">
                          Error: {offer.errors[0]}
                        </p>
                      )}
                    </div>

                    <div className="text-right text-sm text-muted-foreground">
                      <div>
                        Started: {formatDistanceToNow(new Date(offer.created_at), { addSuffix: true })}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
