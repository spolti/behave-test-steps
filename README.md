# Cekit Behave steps

This repository contains test steps for the [Behave library](https://github.com/behave/behave) used in the [Cekit tool](https://github.com/cekit/cekit/).

## Why external repository?

Because the test steps are rapidly changing by adding new steps or adjusting existing ones
it does not make sense to combine it together with Cekit releases. These do have different lifecycle. We decided to separate these and so far it's working well.

## Dependencies (Cekit 3.0+)

Because test steps have different requirements and these can change over time, Cekit introduced a weak dependency mechanism (see https://github.com/cekit/cekit/pull/357 for more information). In this steps library it is implemented in the `loader.py` file which defines what dependencies are required.

This information will let Cekit check **at runtime** if requirements are met and if not, user will be notified. If you are running on a known platform, in case a depenency is missing, you will be provided with a hint what to install to satisfy the requirement.
