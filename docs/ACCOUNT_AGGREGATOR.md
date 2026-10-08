# Account Aggregator (auto-sync bank data): findings

Goal: let a user connect their bank once and have SaverAI read transactions automatically, instead of uploading CSV/PDF statements.

## What it is
India's Account Aggregator (AA) framework lets a user consent to share bank data (digitally signed) from a Financial Information Provider (their bank) to a Financial Information User (FIU) through an RBI-licensed Account Aggregator.

## The blocker for SaverAI
Per Sahamati, "entities who want to become FIUs need to be registered and regulated by at least any one of the Financial Service Regulators (RBI, SEBI, IRDAI, PFRDA)". A new unregulated app cannot be a direct FIU.
Source: https://sahamati.org.in/fiu/

## Realistic paths
1. Partner with an already-regulated FIU or a Technical Service Provider that offers FIU modules ("available from Technical Service Providers that you could use readily"). Source: https://sahamati.org.in/how-to-join-the-account-aggregator-network-to-share-and-access-financial-data/
2. Become regulated first (heavy: licensing, capital, compliance). Not a seed-stage move.
3. Keep statement import (CSV/PDF, already built) as the no-regulation path, and add AA later through a partner.

## If we go ahead (technical steps from Sahamati)
Implement the ReBIT FIU APIs and callbacks, test in AA sandboxes (OneMoney, Finvu, NADL and others), enrol in the UAT registry, get certified by an empanelled certifier, then be added to the live registry.

## Governing rules
RBI Master Directions for NBFC Account Aggregators, 2025: https://rbi.org.in/scripts/BS_ViewMasDirections.aspx?id=12936

## Recommendation
Do not build AA integration yet. Talk to one or two AA/TSP partners once there are real users, and keep CSV/PDF import as the default. Nothing here has been checked with a lawyer or a partner.
