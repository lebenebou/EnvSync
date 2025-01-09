# MUREX CLI
Manipulate GQAF, Jira and more through the command line.
Requires python 3.6.8 or later.
Below are some usage examples. Feel free to also use `--help` for any script.

## View Setups
`gqaf/setups.py -v <version>`
### Example Output:
```cmd
deployer      changelist  buildId                      status    operatingSystem        deployDate       
----------  ------------  ---------------------------  --------  ---------------------  --------------- 

mhachem          7398133  7398133-241128-0830-6640014  DONE      Linux-rhel-8.6-x86_64  Nov 28 08:30 AM
mhachem          7398125  7398125-241128-0759-6639966  STOPPED   Linux-rhel-8.6-x86_64  Nov 28 08:00 AM
ci-assets        7396221  7396221-241126-2217-6637899  DONE      Windows-x86-5.2-64b    Nov 26 10:19 PM
ci-assets        7396221  7396221-241126-2217-6637898  DONE      Linux-rhel-8.6-x86_64  Nov 26 10:19 PM
pyammine         7395703  7395703-241126-1702-6637349  DONE      Windows-x86-5.2-64b    Nov 26 05:03 PM
pyammine         7395703  7395703-241126-1702-6637348  DONE      Linux-rhel-8.6-x86_64  Nov 26 05:02 PM
...
```

### Other ways to do it:
Get latest setups: use `--latest`
Filter by changelist: use `-cl <changelist>`
Filter by user: use `-u <username>`
Filter by current user: use `--me`

## View Deployment Jobs
`gqaf/jobs.py -v <version>`
### Example Output:
```cmd
testPackage      nickname                id                 status    owner     pushDate           changelist
---------------  ----------------------  -----------------  --------  --------  ---------------  ------------

PAR.TPK.0002786  BOND_SaaSSerialization  PAR.DJOB.75056179  PASSED    rzaatari  Nov 29 02:19 PM       7400272
PAR.TPK.0002914  BOND_SERIES             PAR.DJOB.75056178  PASSED    rzaatari  Nov 29 02:19 PM       7400272
PAR.TPK.0002923  DEFAULT                 PAR.DJOB.75056177  PASSED    rzaatari  Nov 29 02:19 PM       7400272
PAR.TPK.0001918  DEFAULT                 PAR.DJOB.75056176  PASSED    rzaatari  Nov 29 02:19 PM       7400272
...
```

### Other ways to do it:
Filter by changelist: use `-cl <changelist>`
Get jobs at latest setups: use `--latest`
Filter by user: use `-u <username>`
Filter by current user: use `--me`

## Push Setups
`gqaf/pushSetups.py -v <version> -cl <changelist> --linux`
### Example Output:
```cmd
Setups pushed.
{
    "version": "v3.1.build.dev.a7.li.199458.094",
    "changelist": "7400014",
    "owner": "yoyammine",
    "operatingSystems": [
        "Linux-rhel-8.6-x86_64"
    ],
    "commandId": 2090690
}
```
### Other ways to do it:
Push setups at head: use `--head`
Push setups at shelved changelist on top of main changelist: use `-cl <mainCL> --shelved-cl <shelvedCL>`
Push windows setups: use `--windows`

## Get Submitted Changelists
`p4helper.py -v <version> -u <user>`

Gets chagelists submitted by `user` on `srcVersion`
### Example Output:
```cmd
CL 7403263 by yoyammine - [DEF0607259][BondsAndFuturesPri...
CL 7396144 by yoyammine - [DEF0604080] [BondsAndFuturesPr...
CL 7396146 by yoyammine - [DEF0604083] [BondsAndFuturesPr...
...
```

## Get Changelists Unmerged On Build
`p4helper.py -u <user> -v <srcVersion> --unmerged`

Gets chagelists submitted by `user` on `srcVersion`, but not merged on `v3.1.build` (by defectID)
### Example Output:
```cmd
yoyammine's Cls on v3.1.build.dev.a7.li.200090.097 not yet on v3.1.build:
CL 7403263 by yoyammine - [DEF0607259]  [BondsAndFuturesPrices][Refactoring] offline test Price Quotation column
...
```