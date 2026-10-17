within;
package IGCObservationCore
  partial model Upstream
    extends IGCTransitCore.Upstream;
    Real reportedDeliveryRate "Displayed, potentially filtered physical delivery rate";
  end Upstream;
  annotation(uses(Modelica(version="4.0.0"),SystemDynamics(version="2.1.2")));
end IGCObservationCore;
