---
title: Plan and Outline
subtitle: General overview on Publication Plan of Indonesia GeoMAD National Production
---
---

## Title Options:
 1. Cloud-Native GeoMAD Production at National Scale Using Open Data Cube and Adaptive Resource Allocation in Indonesia
 2. A Scalable Cloud-Native Workflow for Cost-Efficient National GeoMAD Compositing Using Open Data Cube
 3. Optimizing National-Scale Sentinel-2 GeoMAD Production Through Cloud-Native Processing and Adaptive Resource Allocation
 4. Cost-Efficient National GeoMAD Production Using Cloud-Native Open Data Cube Workflows and Adaptive Resource Allocation

## Target Publications:
      
- International Journal of Applied Earth Observation and Geoinformation - [Aim and Scope](https://www.sciencedirect.com/journal/international-journal-of-applied-earth-observation-and-geoinformation/about/aims-and-scope)
    - _Keywords_: big spatiotemporal data, expand existing methodology, the state-of-the-art methods, convey important recommendations (reproducible workflows for national production in Indonesia)
- Remote Sensing (MDPI) - [Aim and Scope](https://www.mdpi.com/journal/remotesensing/about)
    - _Keywords_: Remote Sensing Application


## PAPER OUTLINE

### 1. INTRODUCTION

**1.1 Background**
- National-scale Earth observation processing requirements
- GeoMAD as temporal composite methodology for baseline mapping
- Challenges in tropical regions: persistent cloud cover, data volume, computational costs

**1.2 Problem Statement**
Operational implementation of national-scale GeoMAD processing presents three interconnected challenges:
- Balancing data quality through cloud filtering with temporal coverage requirements
- Optimizing computational resource allocation across heterogeneous processing workloads
- Minimizing processing costs while maintaining reproducibility and scalability

**1.3 Research Objectives**
This study presents a reproducible cloud-native workflow for national-scale GeoMAD production using Open Data Cube and Kubernetes-based orchestration, demonstrated through Indonesia's 2024 Sentinel-2 archive. Specific objectives include:
- Systematic evaluation of cloud cover threshold optimization strategies
- Development of data-driven resource allocation approaches based on tile characteristics
- Quantification of cost-benefit trade-offs comparing optimized versus baseline processing
- Provision of open-source implementation enabling methodology replication

**1.4 Contributions**
- Transferable workflow adaptable to diverse geographic and computational contexts
- Open-source implementation with documented configurations
- Data-driven framework for cloud cover filtering and resource allocation optimization
- Quantified cost-benefit analysis demonstrating processing efficiency gains
- Publicly accessible validation datasets and outputs

---

### 2. STUDY AREA AND DATA

**2.1 Study Area**
- Indonesia: geographic extent, land area, maritime proportion
- Tropical climate characteristics and cloud cover implications
- National mapping requirements and context

**2.2 Data**
- Sentinel-2 Level 2A surface reflectance products
- Temporal coverage: 2024 calendar year
- Data volume and spatial extent
- Open Data Cube indexing and management

**2.3 Computational Infrastructure**
- Amazon Web Services cloud environment
- Kubernetes container orchestration
- Argo Workflows for distributed processing
- Output delivery via public S3 bucket

---

### 3. METHODOLOGY

**3.1 Workflow Architecture**

Four-phase processing framework:

Phase 1: Data Preparation
- Open Data Cube indexing of Sentinel-2 archive
- Spatial filtering using administrative boundaries
- Ocean tile exclusion strategy
- Task generation using odc-stats

Phase 2: Optimization Testing
- Cloud cover threshold experimentation (60%, 80%, 100%)
- Stratified tile sampling across data availability gradients
- Resource profiling with comprehensive metrics logging

Phase 3: Adaptive Configuration
- Tile classification based on dataset count and observation days
- Resource allocation matrix development
- Multi-workflow Argo configuration design

Phase 4: Production and Validation
- Distributed processing execution
- Two-tier quality assessment
- Public data release with metadata

**3.2 Spatial Coverage Optimization**

Land-ocean discrimination approach:
- Administrative boundary masking using national geospatial datasets
- Grid tile intersection analysis
- Tile retention criteria and validation
- Coverage statistics and spatial distribution

**3.3 Cloud Cover Threshold Optimization**

Experimental Design:
- Three threshold scenarios: 60%, 80%, 100% maximum cloud cover
- Stratified sampling: 11 tiles across four data availability categories
  - Group 1: Low reduction baseline (minimal threshold impact)
  - Group 2: Low absolute data with high reduction
  - Group 3: Medium absolute data with high reduction
  - Group 4: High absolute data with high reduction
- Processing: Each tile processed under all three thresholds
- Comparative metrics: data retention, output quality, resource consumption

Validation Framework:

Tier 1: Automated Statistical Assessment
- Spatial completeness (valid pixel ratio)
- MAD stability (median absolute deviation metrics)
- Temporal coverage (observation day distribution)
- Cloud contamination detection

Tier 2: Expert Visual Assessment
- Three independent assessors from national mapping agency
- Blind evaluation protocol with randomized presentation
- Standardized criteria: overall quality, artifact presence, operational fitness
- Inter-rater reliability analysis using Fleiss' kappa

**3.4 Resource Profiling and Adaptive Allocation**

Profiling Experiment:
- Test environment: AWS r7.4xlarge instances (16 vCPU, 128 GB RAM)
- Monitoring metrics: peak memory usage, CPU utilization, processing time
- Logging implementation via Kubernetes metrics collection

Analysis:
- Statistical modeling: peak memory as function of dataset count and observation days
- Correlation analysis between tile characteristics and resource requirements
- Resource class boundary determination

Implementation:
- Resource classification matrix development
- Multi-workflow Argo configuration with dynamic task routing
- Parallel execution across resource classes
- Adaptive cloud cover threshold assignment based on tile characteristics

**3.5 Cost Analysis**

Baseline Scenario:
- All tiles processed including ocean coverage
- No cloud cover filtering (100% threshold)
- Uniform instance type allocation
- Cost calculation: total tiles × average processing time × instance hourly rate

Optimized Scenario:
- Spatial filtering applied (land tiles only)
- Adaptive cloud cover thresholds (60% or 80% based on tile class)
- Right-sized instance allocation per resource class
- Cost calculation: sum across tile classes (tiles × time × class-specific rate)

Savings Analysis:
- Component breakdown: spatial filtering, cloud filtering, right-sizing
- Percentage reduction calculation
- Sensitivity analysis across cost parameters

---

### 4. RESULTS

**4.1 Spatial Coverage Optimization**
- Tile retention statistics
- Ocean exclusion effectiveness
- Spatial distribution of retained tiles

**4.2 Cloud Cover Threshold Impact**
- Data availability comparison across thresholds
- Dataset count and observation day distributions
- Temporal coverage analysis

**4.3 Quality Assessment Results**

Tier 1 Automated Metrics:
- Spatial completeness across tiles and thresholds
- MAD stability patterns
- Temporal coverage adequacy
- Cloud contamination scores

Tier 2 Expert Assessment:
- Quality score distributions
- Artifact detection frequencies
- Operational fitness ratings
- Inter-rater agreement statistics

**4.4 Resource Consumption Patterns**
- Memory usage versus dataset count relationship
- Processing time distributions
- Resource class boundary validation
- Recommended instance type allocation matrix

**4.5 Cost-Benefit Analysis**
- Baseline processing cost estimation
- Optimized processing cost calculation
- Total savings quantification
- Component-wise savings breakdown
- Cost per tile distributions

---

### 5. DISCUSSION

**5.1 Cloud Cover Threshold Selection**
- Trade-offs between data quality and temporal coverage
- Recommendations for tropical versus temperate regions
- Seasonal considerations and temporal gaps

**5.2 Resource Allocation Strategy**
- Effectiveness of data-driven right-sizing
- Computational efficiency gains
- Scalability considerations for larger deployments

**5.3 Cost Optimization**
- Primary cost drivers and mitigation strategies
- Comparison with traditional HPC approaches
- Economic feasibility for operational programs

**5.4 Methodology Transferability**
- Applicability to other geographic regions
- Adaptation requirements for different sensors or products
- Limitations and boundary conditions

**5.5 Operational Considerations**
- Implementation requirements for national mapping agencies
- Technical capacity and infrastructure needs
- Data management and delivery strategies

**5.6 Limitations**
- Atoll and small island coverage gaps
- Single-year demonstration scope
- Validation sample size constraints
- Cloud detection algorithm dependencies

---

### 6. CONCLUSIONS

- Summary of workflow effectiveness and cost reduction achievements
- Key findings on cloud cover optimization and resource allocation
- Practical implications for operational Earth observation programs
- Contribution to reproducible and scalable national mapping methodologies
- Future research directions: multi-year production, automated quality control, expanded validation

---

## SUPPLEMENTARY MATERIALS

- Complete odc-stats configuration files
- Argo Workflows YAML specifications
- Kubernetes resource definitions
- Tile classification algorithm implementation
- Statistical analysis scripts
- Validation protocols and assessment forms
- Cost calculation spreadsheets

---

## KEY FIGURES

Figure 1: Study area map with ODC grid overlay and tile distribution statistics

Figure 2: Cloud cover threshold impact on data availability (box plots and retention percentages)

Figure 3: Resource consumption analysis (scatter plot with regression model and resource class boundaries)

Figure 4: Validation results summary (automated metrics heatmap and expert assessment distributions)

Figure 5: Visual quality comparison across cloud cover thresholds (multi-panel tile examples)

Figure 6: Cost-benefit analysis (baseline versus optimized comparison with savings breakdown)

Figure 7: Workflow architecture diagram with decision points and implementation details

---

## KEY TABLES

Table 1: Tile sampling strategy and characteristics across four data availability groups

Table 2: Cloud cover threshold scenarios and resulting data retention statistics

Table 3: Resource allocation matrix with instance type recommendations

Table 4: Cost analysis summary comparing baseline and optimized scenarios

Table 5: Validation metrics summary across tiles and cloud cover thresholds
