// Rule 1: Emergency Trip authorized if within tenant zone AND physical bounds OR Bedrock surge risk breached
permit (
    principal,
    action == Action::"TripFeederRelay",
    resource
)
when {
    context.operatorZone == context.transformerZone &&
    (
        context.waterLevelCm > 20 || 
        context.neutralCurrentAmps > 40 || 
        context.phaseRVolts < 50 ||
        (context.waterLevelCm > 12 && context.mlFloodSurgeRiskPercent > 80)
    )
};

permit (
    principal,
    action == Action::"DispatchLinemanTicket",
    resource
);

forbid (
    principal,
    action == Action::"ResetFeederRelay",
    resource
)
when {
    context.oilTempCelsius > 70
};
