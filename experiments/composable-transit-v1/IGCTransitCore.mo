within;
package IGCTransitCore
  partial model Upstream
    "Previously tested finite preparation and dispatch queues; downstream is selected by graph"
    extends IGCS2MakeToOrder.Scenario;
    parameter Real transitCapacity=100 "Trusted backend maximum shipment movements/hour";
    parameter Real transitResponseTime=1.5 "Trusted backend mean transit residence time/hour";
    IGCMolecules.AcceptedSource accepted;
    IGCMolecules.BoundedQueue preparation(
      maxThroughput=capacityPreparing,
      responseTime=preparationResponseTime);
    IGCMolecules.BoundedQueue dispatch(
      maxThroughput=capacityDispatch,
      responseTime=dispatchResponseTime);
    IGCMolecules.DeliveryCounter delivered;
    Real deliveryRate "Shipment received per hour";
    Real inTransit "Shipped units not yet received";
  equation
    accepted.externalRate = acceptedRate;
    connect(accepted.outflow,preparation.arrival);
    connect(preparation.completed,dispatch.arrival);
    unpreparedOrders = preparation.waiting;
    preparedOrders = dispatch.waiting;
    preparationRate = preparation.completed;
    dispatchRate = dispatch.completed;
    deliveredOrders = delivered.total;
  end Upstream;
  annotation(uses(Modelica(version="4.0.0"),SystemDynamics(version="2.1.2")));
end IGCTransitCore;
