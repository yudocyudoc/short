within;
package IGCV3FoundationSmoke
  "Engineering regression fixture only; not a hidden-world or inference task"
  partial model PhysicalPath
    Modelica.Blocks.Sources.Pulse orders(
      amplitude=6, period=4, width=40, startTime=1);
    IGCMolecules.AcceptedSource source;
    IGCMolecules.BoundedQueue queue(
      maxThroughput=5, responseTime=0.75);
    IGCMolecules.DeliveryCounter delivered;
    Real acceptedRate;
    Real physicalDeliveryRate;
    Real waitingStock;
    Real totalDelivered;
  equation
    connect(orders.y,source.externalRate);
    connect(source.outflow,queue.arrival);
    connect(queue.completed,delivered.arrival);
    acceptedRate = source.outflow;
    physicalDeliveryRate = queue.completed;
    waitingStock = queue.waiting;
    totalDelivered = delivered.total;
  end PhysicalPath;

  model Direct
    extends PhysicalPath;
    Real reportedDeliveryRate;
  equation
    reportedDeliveryRate = physicalDeliveryRate;
  end Direct;

  model Filtered
    extends PhysicalPath;
    IGCInformationMolecules.FirstOrderReportFilter report(
      reportResponseTime=0.8);
    Real reportedDeliveryRate;
  equation
    connect(queue.completed,report.physicalArrivalRate);
    reportedDeliveryRate = report.reportedRate;
  end Filtered;
  annotation(uses(Modelica(version="4.0.0"),SystemDynamics(version="2.1.2")));
end IGCV3FoundationSmoke;
