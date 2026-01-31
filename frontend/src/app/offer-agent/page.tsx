import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, FileText, Clock, CheckCircle } from "lucide-react";
import Link from "next/link";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Overview of your offer automation system
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Active Offers
            </CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">--</div>
            <p className="text-xs text-muted-foreground">
              Currently processing
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Pending Review
            </CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">--</div>
            <p className="text-xs text-muted-foreground">
              Awaiting approval
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Completed Today
            </CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">--</div>
            <p className="text-xs text-muted-foreground">
              Sent to ERP
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Total This Month
            </CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">--</div>
            <p className="text-xs text-muted-foreground">
              All processed offers
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>
              Common tasks and shortcuts
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-2">
            <Link
              href="/offer-agent/offers/create"
              className="flex items-center rounded-lg border p-3 hover:bg-accent"
            >
              <FileText className="mr-3 h-5 w-5" />
              <div>
                <div className="font-medium">Create New Offer</div>
                <div className="text-sm text-muted-foreground">
                  Manually create a new offer request
                </div>
              </div>
            </Link>
            <Link
              href="/offer-agent/offers/review"
              className="flex items-center rounded-lg border p-3 hover:bg-accent"
            >
              <Clock className="mr-3 h-5 w-5" />
              <div>
                <div className="font-medium">Review Pending Offers</div>
                <div className="text-sm text-muted-foreground">
                  Check and approve pending offers
                </div>
              </div>
            </Link>
            <Link
              href="/offer-agent/monitoring"
              className="flex items-center rounded-lg border p-3 hover:bg-accent"
            >
              <Activity className="mr-3 h-5 w-5" />
              <div>
                <div className="font-medium">View Processing Status</div>
                <div className="text-sm text-muted-foreground">
                  Monitor offers being processed
                </div>
              </div>
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>System Status</CardTitle>
            <CardDescription>
              Backend service health
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm">Offer Agent API</span>
                <span className="flex items-center text-sm text-yellow-600">
                  <span className="mr-2 h-2 w-2 rounded-full bg-yellow-500" />
                  Not connected
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Email Processor</span>
                <span className="flex items-center text-sm text-yellow-600">
                  <span className="mr-2 h-2 w-2 rounded-full bg-yellow-500" />
                  Unknown
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">ERP Connection</span>
                <span className="flex items-center text-sm text-yellow-600">
                  <span className="mr-2 h-2 w-2 rounded-full bg-yellow-500" />
                  Unknown
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
