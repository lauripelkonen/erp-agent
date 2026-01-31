"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { useClientConfig } from "@/hooks/use-client-config";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Save, RefreshCw } from "lucide-react";

export default function SettingsPage() {
  const { toast } = useToast();
  const { config, setClientId, availableClients, isLoading } = useClientConfig();
  const [apiUrl, setApiUrl] = useState(
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
  );
  const [isTesting, setIsTesting] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<
    "unknown" | "connected" | "error"
  >("unknown");

  const testConnection = async () => {
    setIsTesting(true);
    try {
      const response = await fetch("/api/health");
      if (response.ok) {
        setConnectionStatus("connected");
        toast({
          title: "Connection Successful",
          description: "Successfully connected to the backend API",
        });
      } else {
        setConnectionStatus("error");
        toast({
          title: "Connection Failed",
          description: "Could not connect to the backend API",
          variant: "destructive",
        });
      }
    } catch (error) {
      setConnectionStatus("error");
      toast({
        title: "Connection Error",
        description: "Failed to reach the backend server",
        variant: "destructive",
      });
    } finally {
      setIsTesting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">
          Configure your ERP Agent frontend
        </p>
      </div>

      <div className="grid gap-6">
        <Card>
          <CardHeader>
            <CardTitle>API Configuration</CardTitle>
            <CardDescription>
              Configure the connection to your offer-agent backend
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="apiUrl">Backend API URL</Label>
              <div className="flex gap-2">
                <Input
                  id="apiUrl"
                  value={apiUrl}
                  onChange={(e) => setApiUrl(e.target.value)}
                  placeholder="http://localhost:8000"
                />
                <Button
                  variant="outline"
                  onClick={testConnection}
                  disabled={isTesting}
                >
                  {isTesting ? (
                    <RefreshCw className="h-4 w-4 animate-spin" />
                  ) : (
                    "Test"
                  )}
                </Button>
              </div>
              <p className="text-sm text-muted-foreground">
                Status:{" "}
                <span
                  className={
                    connectionStatus === "connected"
                      ? "text-green-600"
                      : connectionStatus === "error"
                      ? "text-red-600"
                      : "text-yellow-600"
                  }
                >
                  {connectionStatus === "connected"
                    ? "Connected"
                    : connectionStatus === "error"
                    ? "Connection Error"
                    : "Not tested"}
                </span>
              </p>
            </div>

            <p className="text-sm text-muted-foreground">
              Note: The API URL is configured via environment variables. To
              change it permanently, update the NEXT_PUBLIC_API_URL in your
              .env.local file.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Client Configuration</CardTitle>
            <CardDescription>
              Configure client-specific settings for the review page
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Active Client Profile</Label>
              <Select
                value={config?.clientId || "default"}
                onValueChange={setClientId}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a client profile" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="default">Default</SelectItem>
                  {availableClients.map((client) => (
                    <SelectItem key={client} value={client}>
                      {client}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-sm text-muted-foreground">
                Different clients can have different column configurations in
                the review page
              </p>
            </div>

            {config && (
              <div className="rounded-lg border p-4 space-y-2">
                <h4 className="font-medium">Current Configuration</h4>
                <div className="text-sm space-y-1">
                  <p>
                    <span className="text-muted-foreground">Client:</span>{" "}
                    {config.clientName}
                  </p>
                  <p>
                    <span className="text-muted-foreground">Show Pricing:</span>{" "}
                    {config.showPricing ? "Yes" : "No"}
                  </p>
                  <p>
                    <span className="text-muted-foreground">
                      Visible Columns:
                    </span>{" "}
                    {config.columnConfig.filter((c) => c.visible).length} of{" "}
                    {config.columnConfig.length}
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>About</CardTitle>
            <CardDescription>
              ERP Agent Offer Automation Frontend
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm">
              <p>
                <span className="text-muted-foreground">Version:</span> 0.1.0
              </p>
              <p>
                <span className="text-muted-foreground">Framework:</span>{" "}
                Next.js 15
              </p>
              <p>
                <span className="text-muted-foreground">Deployment:</span>{" "}
                Vercel
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
