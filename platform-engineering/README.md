# Information

```bash
❯ oc get projects
NAME             DISPLAY NAME   STATUS
sasya-chikitsa                  Active


cd ../platform-engineering/
total 24
-rw-r--r--@ 1 rajranja  staff   1.1K 20 Aug 15:19 deployment.yaml
-rw-r--r--@ 1 rajranja  staff   591B 20 Aug 15:27 route.yaml
-rw-r--r--@ 1 rajranja  staff   568B 20 Aug 15:23 service.yaml


❯ oc apply -f .
deployment.apps/engine created
route.route.openshift.io/engine created
service/engine created


❯ oc get all
Warning: apps.openshift.io/v1 DeploymentConfig is deprecated in v4.14+, unavailable in v4.10000+
NAME                          READY   STATUS    RESTARTS   AGE
pod/engine-759f54cc79-45nhr   1/1     Running   0          2m58s

NAME             TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
service/engine   ClusterIP   172.30.150.97   <none>        8080/TCP   2m56s

NAME                     READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/engine   1/1     1            1           2m59s

NAME                                DESIRED   CURRENT   READY   AGE
replicaset.apps/engine-759f54cc79   1         1         1       2m59s

NAME                              HOST/PORT                                                                PATH   SERVICES   PORT       TERMINATION     WILDCARD
route.route.openshift.io/engine   engine-sasya-chikitsa.apps.cluster-mx6z7.mx6z7.sandbox5315.opentlc.com          engine     8080-tcp   edge/Redirect   None


```
