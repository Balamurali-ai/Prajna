/**
 * ====================================================
 * 404 Not Found
 * ====================================================
 */
import { Link } from 'react-router-dom'
import { AlertTriangle } from 'lucide-react'

import { Button, Card, CardContent } from '@components/ui'

export function NotFoundPage() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center p-6">
      <Card>
        <CardContent className="flex flex-col items-center gap-4 p-12 text-center">
          <AlertTriangle className="h-12 w-12 text-yellow-500" />
          <div>
            <h1 className="text-2xl font-bold">404</h1>
            <p className="text-muted-foreground">Page not found</p>
          </div>
          <Link to="/dashboard">
            <Button>Go to Dashboard</Button>
          </Link>
        </CardContent>
      </Card>
    </div>
  )
}
