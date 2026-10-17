within;
package IGCBehaviorProbes
  model NoOrdersMTO
    extends IGCS2MakeToOrder.Components(beforeRush=0,duringRush=0);
  end NoOrdersMTO;
  model NoOrdersMTS
    extends IGCS1Parity.Components(acceptedOrders=0,backlog0=0,inventory0=0);
  end NoOrdersMTS;
end IGCBehaviorProbes;
