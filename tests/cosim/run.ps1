$env:RUST_BACKTRACE="full"

Push-Location D:\srcctrl\github\pyfmu

pyfmu export --project .\examples\projects\BicycleDriver --output .\examples\exported\BicycleDriver
pyfmu export --project .\examples\projects\BicycleDynamic --output .\examples\exported\BicycleDynamic

Pop-Location

Remove-Item -Force coe.log

java -jar "D:\srcctrl\github\maestro\orchestration\coe\target\coe-1.0.11-SNAPSHOT-jar-with-dependencies.jar" -v --configuration .\coe.json --oneshot --starttime 0.0 --endtime 10.0
