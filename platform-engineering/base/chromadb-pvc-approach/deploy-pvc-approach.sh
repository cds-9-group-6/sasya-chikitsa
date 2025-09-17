#!/bin/bash

# Deploy ChromaDB with PVC approach on OpenShift
set -e

echo "🚀 Deploying ChromaDB with PVC approach..."

# Get current namespace
NAMESPACE=$(oc project -q)
echo "📍 Using namespace: $NAMESPACE"

# Replace namespace placeholder in all files
for file in *.yaml; do
    if [ -f "$file" ]; then
        sed -i.bak "s/your-namespace/$NAMESPACE/g" "$file"
        rm "$file.bak"
        echo "✅ Updated namespace in $file"
    fi
done

# Apply manifests in order
echo "📦 Creating PVC..."
oc apply -f 01-pvc.yaml

echo "⚙️ Creating ConfigMap..."
oc apply -f 02-configmap.yaml

echo "🔄 Creating Deployment..."
oc apply -f 03-deployment.yaml

echo "🌐 Creating Service..."
oc apply -f 04-service.yaml

echo "🛣️ Creating Route..."
oc apply -f 05-route.yaml

echo "💾 Running data loader job..."
oc apply -f 06-data-loader-job.yaml

# Wait for PVC to be bound
echo "⏳ Waiting for PVC to be bound..."
oc wait --for=condition=Bound pvc/chromadb-data-pvc --timeout=60s

# Wait for deployment to be ready
echo "⏳ Waiting for deployment to be ready..."
oc wait --for=condition=Available deployment/chromadb --timeout=300s

# Get the route URL
ROUTE_URL=$(oc get route chromadb-route -o jsonpath='{.spec.host}')
echo "🎉 ChromaDB is ready!"
echo "📍 Access URL: https://$ROUTE_URL"
echo ""
echo "📋 Next steps:"
echo "1. Copy your data to the PVC:"
echo "   POD_NAME=\$(oc get pods -l app=chromadb -o jsonpath='{.items[0].metadata.name}')"
echo "   oc rsync ./chroma_capstone_db_new/ \$POD_NAME:/chroma/chroma/"
echo ""
echo "2. Restart the deployment after copying data:"
echo "   oc rollout restart deployment/chromadb"
echo ""
echo "3. Test the connection:"
echo "   curl https://$ROUTE_URL/api/v1/heartbeat"
